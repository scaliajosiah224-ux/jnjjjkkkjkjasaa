"""Pydantic models for user-related requests and responses"""
from pydantic import BaseModel, EmailStr
from typing import Optional

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    username: str
    display_name: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    avatar_color: Optional[str] = None
