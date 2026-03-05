"""Pydantic models for messaging-related requests"""
from pydantic import BaseModel
from typing import Optional

class SendSMSRequest(BaseModel):
    to_number: str
    message: str
    from_number: Optional[str] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None

class ConversationRequest(BaseModel):
    recipient_number: str
    recipient_name: Optional[str] = None

class ReactToMessageRequest(BaseModel):
    message_id: str
    emoji: str

class ReadReceiptRequest(BaseModel):
    conversation_id: str
