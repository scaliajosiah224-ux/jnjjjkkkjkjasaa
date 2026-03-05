"""Voicemail routes"""
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from routes.dependencies import get_db, get_current_user

router = APIRouter(prefix="/api/voicemail", tags=["voicemail"])

@router.get("")
async def get_voicemails(user=Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get user's voicemails."""
    voicemails = await db.voicemails.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"voicemails": voicemails}
