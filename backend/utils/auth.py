"""Authentication utilities"""
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Load environment variables early
load_dotenv()

JWT_SECRET = os.environ.get("JWT_SECRET", "ringring_secret_2025")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXP_HOURS = int(os.environ.get("JWT_EXPIRATION_HOURS", "24"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain, hashed)

def create_token(user_id: str, email: str) -> str:
    """Create a JWT token for user authentication"""
    exp = datetime.utcnow() + timedelta(hours=JWT_EXP_HOURS)
    return jwt.encode({"sub": user_id, "email": email, "exp": exp}, JWT_SECRET, algorithm=JWT_ALGORITHM)
