"""Shared dependencies for routes"""
from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from dotenv import load_dotenv
import os

# Load environment variables early
load_dotenv()

# Database connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "ringring")

client = AsyncIOMotorClient(MONGO_URL)
db_instance = client[DB_NAME]

# JWT settings
JWT_SECRET = os.environ.get("JWT_SECRET", "ringring_secret_2025")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")

security = HTTPBearer()

def get_db() -> AsyncIOMotorDatabase:
    """Dependency to get database instance"""
    return db_instance

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "hashed_password": 0, "password_hash": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
