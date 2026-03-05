"""Pydantic models for Sinch callback requests"""
from pydantic import BaseModel
from typing import Optional

class ICERequest(BaseModel):
    """Incoming Call Event from Sinch"""
    callid: str
    cli: str
    originalcli: Optional[str] = None
    to: str
    domain: str
    timestamp: int
    custom: Optional[str] = None
    callheaders: Optional[dict] = None
    mxp: Optional[dict] = None

class ACERequest(BaseModel):
    """Answered Call Event from Sinch"""
    callid: str
    callResourceUrl: str
    cli: str
    to: str
    domain: str
    timestamp: int
    amd: Optional[dict] = None

class DICERequest(BaseModel):
    """Disconnect Call Event from Sinch"""
    callid: str
    callResourceUrl: str
    reason: str
    timestamp: int
    result: str
