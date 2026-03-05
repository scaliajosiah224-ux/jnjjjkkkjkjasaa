"""Call history and management routes"""
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
import uuid

from routes.dependencies import get_db, get_current_user

router = APIRouter(prefix="/api/calls", tags=["calls"])

@router.get("/history")
async def get_call_history(user=Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get call history."""
    calls = await db.calls.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return {"calls": calls}

@router.post("/log")
async def log_call(call_data: dict, user=Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    """Log a call."""
    call_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "direction": call_data.get("direction", "outbound"),
        "from_number": call_data.get("from_number", ""),
        "to_number": call_data.get("to_number", ""),
        "duration": call_data.get("duration", 0),
        "status": call_data.get("status", "completed"),
        "sinch_call_id": call_data.get("sinch_call_id", ""),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.calls.insert_one(call_doc)
    return {"success": True, "call": {k: v for k, v in call_doc.items() if k != "_id"}}

@router.get("/recent")
async def get_recent_calls(user=Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get recent calls."""
    calls = await db.calls.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(20)
    return {"calls": calls}
