"""Phone number management routes"""
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
import uuid
import os

from models.number import SearchNumbersRequest, PurchaseNumberRequest
from utils.sinch_client import sinch_request
from routes.dependencies import get_db, get_current_user

router = APIRouter(prefix="/api/numbers", tags=["numbers"])

def get_sinch_project_id():
    """Get Sinch project ID at runtime"""
    return os.environ.get("SINCH_PROJECT_ID", "")

@router.get("/sinch-active")
async def get_sinch_active_numbers(user=Depends(get_current_user)):
    """Get all active numbers from Sinch."""
    SINCH_PROJECT_ID = get_sinch_project_id()
    if not SINCH_PROJECT_ID:
        raise HTTPException(status_code=503, detail="Sinch not configured")
    
    url = f"https://numbers.api.sinch.com/v1/projects/{SINCH_PROJECT_ID}/activeNumbers"
    result = await sinch_request("GET", url, use_token_auth=False)
    
    if "error" in result:
        return {"active_numbers": [], "error": result["error"]}
    
    return {"active_numbers": result.get("activeNumbers", [])}

@router.post("/search")
async def search_numbers(req: SearchNumbersRequest, user=Depends(get_current_user)):
    """Search available numbers from Sinch."""
    SINCH_PROJECT_ID = get_sinch_project_id()
    if not SINCH_PROJECT_ID:
        raise HTTPException(status_code=503, detail="Sinch not configured")
    
    url = f"https://numbers.api.sinch.com/v1/projects/{SINCH_PROJECT_ID}/availableNumbers"
    
    params = [
        f"regionCode={req.country_code}",
        f"type={req.number_type or 'LOCAL'}"
    ]
    if req.area_code:
        params.append(f"pattern={req.area_code}*")
    
    full_url = f"{url}?{'&'.join(params)}"
    result = await sinch_request("GET", full_url, use_token_auth=False)
    
    if "error" in result:
        return {"available_numbers": [], "error": result["error"]}
    
    return {"available_numbers": result.get("availableNumbers", [])}

@router.post("/claim")
async def claim_number(
    req: PurchaseNumberRequest,
    user=Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Claim an existing Sinch number for the user."""
    SINCH_PROJECT_ID = get_sinch_project_id()
    if not SINCH_PROJECT_ID:
        raise HTTPException(status_code=503, detail="Sinch not configured")
    
    # Check if number already claimed
    existing = await db.phone_numbers.find_one({
        "phone_number": req.phone_number,
        "user_id": user["id"]
    })
    
    if existing:
        return {"success": True, "message": "Number already claimed", "number": {k: v for k, v in existing.items() if k != "_id"}}
    
    # Save to database
    number_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "phone_number": req.phone_number,
        "is_active": True,
        "claimed_at": datetime.now(timezone.utc).isoformat()
    }
    await db.phone_numbers.insert_one(number_doc)
    
    # Update user's phone_numbers list
    await db.users.update_one(
        {"id": user["id"]},
        {"$addToSet": {"phone_numbers": req.phone_number}}
    )
    
    return {"success": True, "number": {k: v for k, v in number_doc.items() if k != "_id"}}

@router.post("/purchase")
async def purchase_number(
    req: PurchaseNumberRequest,
    user=Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Purchase a new number from Sinch (requires account upgrade)."""
    SINCH_PROJECT_ID = get_sinch_project_id()
    if not SINCH_PROJECT_ID:
        raise HTTPException(status_code=503, detail="Sinch not configured")
    
    url = f"https://numbers.api.sinch.com/v1/projects/{SINCH_PROJECT_ID}/activeNumbers:rent"
    result = await sinch_request("POST", url, {"phoneNumber": req.phone_number}, use_token_auth=False)
    
    if "error" in result:
        return {"success": False, "error": result["error"]}
    
    # Save to database
    number_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "phone_number": req.phone_number,
        "is_active": True,
        "purchased_at": datetime.now(timezone.utc).isoformat()
    }
    await db.phone_numbers.insert_one(number_doc)
    
    await db.users.update_one(
        {"id": user["id"]},
        {"$addToSet": {"phone_numbers": req.phone_number}}
    )
    
    return {"success": True, "number": {k: v for k, v in number_doc.items() if k != "_id"}}

@router.get("/my")
async def get_my_numbers(user=Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get user's phone numbers."""
    numbers = await db.phone_numbers.find({"user_id": user["id"]}, {"_id": 0}).to_list(20)
    return {"numbers": numbers}

@router.delete("/{number_id}")
async def delete_number(
    number_id: str,
    user=Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete a phone number."""
    number = await db.phone_numbers.find_one({"id": number_id, "user_id": user["id"]})
    if not number:
        raise HTTPException(status_code=404, detail="Number not found")
    
    await db.phone_numbers.delete_one({"id": number_id})
    await db.users.update_one(
        {"id": user["id"]},
        {"$pull": {"phone_numbers": number["phone_number"]}}
    )
    
    return {"success": True, "message": "Number deleted"}
