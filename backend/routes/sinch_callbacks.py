"""Sinch callback handlers (ICE, ACE, DiCE)"""
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
from routes.dependencies import get_db
from models.call import ICERequest, ACERequest, DICERequest

router = APIRouter(prefix="/api/sinch", tags=["sinch"])

@router.post("/ice")
async def handle_incoming_call_event(request: ICERequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Handle Incoming Call Event (ICE) callback from Sinch"""
    try:
        print(f"[ICE] Call: {request.callid}, From: {request.cli}, To: {request.to}, Domain: {request.domain}")
        
        if request.domain == "mxp":
            # App-to-app call - route to user
            target_user_id = request.to.replace("+", "")  # Extract user ID from number
            if request.mxp:
                target_user_id = request.mxp.get("userid", target_user_id)
            
            action = {
                "name": "connectMxp",
                "destination": {
                    "type": "username",
                    "endpoint": target_user_id
                }
            }
        elif request.domain == "pstn":
            # PSTN call - route through conference
            action = {
                "name": "connectConf",
                "destination": {
                    "conferenceId": f"conf-{request.callid}"
                }
            }
        else:
            action = {"name": "hangup"}
        
        return {"action": action, "instructions": []}
    except Exception as e:
        print(f"[ICE] Error: {e}")
        return {"action": {"name": "hangup"}, "instructions": []}

@router.post("/ace")
async def handle_answered_call_event(request: ACERequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Handle Answered Call Event (ACE) callback from Sinch"""
    try:
        print(f"[ACE] Call answered: {request.callid}, Domain: {request.domain}")
        
        # Log the answered call
        await db.calls.update_one(
            {"sinch_call_id": request.callid},
            {"$set": {"status": "answered", "answered_at": datetime.now(timezone.utc).isoformat()}},
            upsert=False
        )
        
        return {"action": {"name": "continue"}, "instructions": []}
    except Exception as e:
        print(f"[ACE] Error: {e}")
        return {"action": {"name": "continue"}}

@router.post("/dice")
async def handle_disconnect_call_event(request: DICERequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Handle Disconnect Call Event (DiCE) callback from Sinch"""
    try:
        print(f"[DiCE] Call ended: {request.callid}, Reason: {request.reason}, Result: {request.result}")
        
        # Update call record
        await db.calls.update_one(
            {"sinch_call_id": request.callid},
            {"$set": {
                "status": "completed",
                "end_reason": request.reason,
                "result": request.result,
                "ended_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=False
        )
        
        return {}
    except Exception as e:
        print(f"[DiCE] Error: {e}")
        return {}
