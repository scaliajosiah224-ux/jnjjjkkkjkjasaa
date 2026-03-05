"""Authentication routes"""
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid
from datetime import datetime, timezone

from models.user import RegisterRequest, LoginRequest, UpdateProfileRequest
from utils.auth import hash_password, verify_password, create_token
from routes.dependencies import get_db, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register")
async def register(req: RegisterRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Register a new user"""
    # Check if user exists
    existing = await db.users.find_one({"email": req.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    existing_username = await db.users.find_one({"username": req.username})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Create user
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": req.email,
        "username": req.username,
        "display_name": req.display_name or req.username,
        "hashed_password": hash_password(req.password),
        "phone_numbers": [],
        "avatar_color": "#8B5CF6",
        "plan": "free",
        "credits": 0.0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    # Generate token
    token = create_token(user_id, req.email)
    
    # Remove sensitive data
    user_doc.pop("hashed_password", None)
    user_doc.pop("_id", None)
    
    return {"token": token, "user": user_doc}

@router.post("/login")
async def login(req: LoginRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Login user"""
    user = await db.users.find_one({"email": req.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check if hashed_password exists
    hashed_pwd = user.get("hashed_password")
    if not hashed_pwd:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not verify_password(req.password, hashed_pwd):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"], user["email"])
    
    # Remove sensitive data before returning
    user.pop("hashed_password", None)
    user.pop("password_hash", None)
    user.pop("_id", None)
    
    return {"token": token, "user": user}

@router.get("/me")
async def get_current_user_info(user=Depends(get_current_user)):
    """Get current user information"""
    return {"user": user}

@router.put("/profile")
async def update_profile(
    req: UpdateProfileRequest,
    user=Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update user profile"""
    update_data = {}
    if req.display_name:
        update_data["display_name"] = req.display_name
    if req.avatar_color:
        update_data["avatar_color"] = req.avatar_color
    
    if update_data:
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": update_data}
        )
    
    # Fetch updated user
    updated_user = await db.users.find_one({"id": user["id"]}, {"_id": 0, "hashed_password": 0})
    return {"user": updated_user}
