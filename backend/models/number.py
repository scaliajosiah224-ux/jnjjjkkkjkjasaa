"""Pydantic models for phone number and contact requests"""
from pydantic import BaseModel
from typing import Optional

class SearchNumbersRequest(BaseModel):
    country_code: str = "US"
    number_type: Optional[str] = "LOCAL"
    area_code: Optional[str] = None

class PurchaseNumberRequest(BaseModel):
    phone_number: str

class AddContactRequest(BaseModel):
    name: str
    phone_number: str
    email: Optional[str] = None
    notes: Optional[str] = None
