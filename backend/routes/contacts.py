"""Contacts management routes"""
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
import uuid

from models.number import AddContactRequest
from routes.dependencies import get_db, get_current_user

router = APIRouter(prefix="/api/contacts", tags=["contacts"])

@router.get("")
async def get_contacts(user=Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get user's contacts."""
    contacts = await db.contacts.find({"user_id": user["id"]}, {"_id": 0}).sort("name", 1).to_list(500)
    return {"contacts": contacts}

@router.post("")
async def add_contact(
    req: AddContactRequest,
    user=Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Add a new contact."""
    contact_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "name": req.name,
        "phone_number": req.phone_number,
        "email": req.email,
        "notes": req.notes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.contacts.insert_one(contact_doc)
    return {"contact": {k: v for k, v in contact_doc.items() if k != "_id"}}

@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: str,
    user=Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete a contact."""
    result = await db.contacts.delete_one({"id": contact_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"success": True, "message": "Contact deleted"}
