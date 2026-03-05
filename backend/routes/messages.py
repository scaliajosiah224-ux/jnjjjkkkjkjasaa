"""Message and conversation routes"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
import uuid
import httpx
import os
import base64

from models.message import SendSMSRequest, ConversationRequest, ReactToMessageRequest, ReadReceiptRequest
from routes.dependencies import get_db, get_current_user

router = APIRouter(prefix="/api/messages", tags=["messages"])

# Sinch configuration
SINCH_SERVICE_PLAN_ID = os.environ.get("SINCH_SERVICE_PLAN_ID", "")
SINCH_SMS_API_TOKEN = os.environ.get("SINCH_SMS_API_TOKEN", "")
KLIPY_API_KEY = os.environ.get("KLIPY_API_KEY", "")

# WebSocket manager will be set from main app
_ws_manager = None

def set_ws_manager(manager):
    global _ws_manager
    _ws_manager = manager

@router.get("/conversations")
async def get_conversations(user=Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get all conversations for the current user."""
    conversations = await db.conversations.find(
        {"participants": user["id"]},
        {"_id": 0}
    ).sort("updated_at", -1).to_list(100)
    return {"conversations": conversations}

@router.post("/conversation")
async def create_or_get_conversation(
    req: ConversationRequest,
    user=Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create or get existing conversation."""
    conv = await db.conversations.find_one({
        "user_id": user["id"],
        "recipient_number": req.recipient_number
    })
    
    if not conv:
        conv_id = str(uuid.uuid4())
        conv = {
            "id": conv_id,
            "user_id": user["id"],
            "participants": [user["id"]],
            "recipient_number": req.recipient_number,
            "recipient_name": req.recipient_name or req.recipient_number,
            "last_message": None,
            "unread_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.conversations.insert_one(conv)
    
    messages = await db.messages.find(
        {"conversation_id": conv["id"]},
        {"_id": 0}
    ).sort("created_at", 1).to_list(200)
    
    conv_data = {k: v for k, v in conv.items() if k != "_id"}
    conv_data["messages"] = messages
    return conv_data

@router.get("/{conversation_id}")
async def get_messages(
    conversation_id: str,
    user=Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get messages for a conversation."""
    conv = await db.conversations.find_one({"id": conversation_id, "user_id": user["id"]})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = await db.messages.find(
        {"conversation_id": conversation_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(200)
    
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": {"unread_count": 0}}
    )
    
    return {"messages": messages}

@router.post("/send")
async def send_message(
    req: SendSMSRequest,
    user=Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Send SMS via Sinch."""
    user_numbers = await db.phone_numbers.find(
        {"user_id": user["id"], "is_active": True},
        {"_id": 0}
    ).to_list(10)
    
    from_number = req.from_number or (user_numbers[0]["phone_number"] if user_numbers else None)
    
    if not from_number:
        raise HTTPException(status_code=400, detail="You need a phone number first")
    
    conv = await db.conversations.find_one({
        "user_id": user["id"],
        "recipient_number": req.to_number
    })
    
    if not conv:
        conv_id = str(uuid.uuid4())
        conv = {
            "id": conv_id,
            "user_id": user["id"],
            "participants": [user["id"]],
            "recipient_number": req.to_number,
            "recipient_name": req.to_number,
            "last_message": req.message,
            "unread_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.conversations.insert_one(conv)
    
    sinch_error = None
    message_status = "sent"
    sinch_result = {}
    
    try:
        sms_url = f"https://us.sms.api.sinch.com/xms/v1/{SINCH_SERVICE_PLAN_ID}/batches"
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                sms_url,
                headers={"Authorization": f"Bearer {SINCH_SMS_API_TOKEN}", "Content-Type": "application/json"},
                json={"from": from_number, "to": [req.to_number], "body": req.message},
                timeout=15.0
            )
            if resp.status_code in [200, 201]:
                sinch_result = resp.json()
            else:
                sinch_error = resp.text
                message_status = "failed"
    except Exception as e:
        sinch_error = str(e)
        message_status = "failed"
    
    msg_id = str(uuid.uuid4())
    message_doc = {
        "id": msg_id,
        "conversation_id": conv["id"],
        "user_id": user["id"],
        "from_number": from_number,
        "to_number": req.to_number,
        "body": req.message,
        "media_url": req.media_url,
        "media_type": req.media_type,
        "direction": "outbound",
        "status": message_status,
        "reactions": {},
        "sinch_batch_id": sinch_result.get("id", ""),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.messages.insert_one(message_doc)
    
    await db.conversations.update_one(
        {"id": conv["id"]},
        {"$set": {
            "last_message": req.message,
            "last_message_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if _ws_manager:
        await _ws_manager.send_to_user(user["id"], {
            "type": "new_message",
            "message": {k: v for k, v in message_doc.items() if k != "_id"}
        })
    
    return {
        "success": message_status == "sent",
        "message": {k: v for k, v in message_doc.items() if k != "_id"},
        "error": sinch_error
    }

@router.post("/upload-media")
async def upload_media(file: UploadFile = File(...), user=Depends(get_current_user)):
    """Upload media file."""
    MAX_FILE_SIZE = 25 * 1024 * 1024
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    
    base64_data = base64.b64encode(contents).decode("utf-8")
    data_url = f"data:{file.content_type};base64,{base64_data}"
    
    return {"url": data_url, "type": file.content_type, "size": len(contents)}

@router.post("/typing")
async def typing_indicator(conversation_id: str, user=Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    """Notify typing."""
    conv = await db.conversations.find_one({"id": conversation_id})
    if conv and _ws_manager:
        for pid in conv.get("participants", []):
            if pid != user["id"]:
                await _ws_manager.send_to_user(pid, {"type": "typing", "conversation_id": conversation_id})
    return {"status": "sent"}

@router.post("/read")
async def mark_as_read(req: ReadReceiptRequest, user=Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    """Mark as read."""
    await db.conversations.update_one({"id": req.conversation_id}, {"$set": {"unread_count": 0}})
    return {"status": "marked_as_read"}

@router.post("/react")
async def react_to_message(req: ReactToMessageRequest, user=Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    """React to message."""
    result = await db.messages.update_one({"id": req.message_id}, {"$set": {f"reactions.{user['id']}": req.emoji}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"status": "reacted"}

# GIF Search - separate router prefix
@router.get("/../gifs/search")
async def search_gifs(q: str = "trending", limit: int = 20, user=Depends(get_current_user)):
    """Search GIFs via Klipy API."""
    if not KLIPY_API_KEY:
        return {"gifs": [], "error": "Klipy API key not configured"}
    
    try:
        async with httpx.AsyncClient() as client:
            base_url = f"https://api.klipy.com/api/v1/{KLIPY_API_KEY}/gifs"
            per_page = min(limit, 50)
            
            if q == "trending":
                url = f"{base_url}/trending?per_page={per_page}&locale=en-US"
            else:
                url = f"{base_url}/search?q={q}&per_page={per_page}&locale=en-US"
            
            resp = await client.get(url, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                gifs = []
                
                gif_data = data.get("data", {}).get("data", [])
                
                for result in gif_data:
                    hd_gif = result.get("file", {}).get("hd", {}).get("gif", {})
                    sd_gif = result.get("file", {}).get("sd", {}).get("gif", {})
                    
                    gif_url = hd_gif.get("url") or sd_gif.get("url")
                    
                    if gif_url:
                        gifs.append({
                            "id": result.get("slug", result.get("id")),
                            "url": gif_url,
                            "preview": sd_gif.get("url", gif_url),
                            "width": hd_gif.get("width", sd_gif.get("width", 200)),
                            "height": hd_gif.get("height", sd_gif.get("height", 200)),
                            "title": result.get("title", "")
                        })
                return {"gifs": gifs}
            else:
                return {"gifs": [], "error": f"Klipy API error: {resp.status_code}"}
    except Exception as e:
        return {"gifs": [], "error": str(e)}
