"""Webhook handlers for Sinch incoming messages"""
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
import uuid

from routes.dependencies import get_db

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

# WebSocket manager will be set from main app
_ws_manager = None

def set_ws_manager(manager):
    global _ws_manager
    _ws_manager = manager

@router.post("/sms/incoming")
async def incoming_sms(request_body: dict, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Handle incoming SMS from Sinch."""
    from_number = request_body.get("from", request_body.get("from_number", ""))
    to_number = request_body.get("to", request_body.get("to_number", ""))
    body = request_body.get("body", request_body.get("message", ""))
    
    if not from_number or not body:
        return {"status": "ok"}
    
    # Find user who owns the to_number
    number_doc = await db.phone_numbers.find_one({"phone_number": to_number, "is_active": True})
    if not number_doc:
        return {"status": "no_user"}
    
    user_id = number_doc["user_id"]
    
    # Find or create conversation
    conv = await db.conversations.find_one({
        "user_id": user_id,
        "recipient_number": from_number
    })
    
    if not conv:
        conv_id = str(uuid.uuid4())
        conv = {
            "id": conv_id,
            "user_id": user_id,
            "participants": [user_id],
            "recipient_number": from_number,
            "recipient_name": from_number,
            "last_message": body,
            "unread_count": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.conversations.insert_one(conv)
    
    # Save incoming message
    msg_id = str(uuid.uuid4())
    message_doc = {
        "id": msg_id,
        "conversation_id": conv["id"],
        "user_id": user_id,
        "from_number": from_number,
        "to_number": to_number,
        "body": body,
        "direction": "inbound",
        "status": "received",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.messages.insert_one(message_doc)
    
    # Update conversation
    await db.conversations.update_one(
        {"id": conv["id"]},
        {"$set": {
            "last_message": body,
            "last_message_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        "$inc": {"unread_count": 1}}
    )
    
    # Notify via WebSocket
    if _ws_manager:
        await _ws_manager.send_to_user(user_id, {
            "type": "new_message",
            "message": {k: v for k, v in message_doc.items() if k != "_id"},
            "conversation_id": conv["id"]
        })
    
    return {"status": "ok"}
