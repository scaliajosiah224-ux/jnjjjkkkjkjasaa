"""Voice calling routes"""
from fastapi import APIRouter, HTTPException, Depends
from routes.dependencies import get_current_user
from utils.sinch_jwt import SinchVoiceJWTGenerator
import os

router = APIRouter(prefix="/api/voice", tags=["voice"])

def get_sinch_voice_credentials():
    """Get Sinch credentials at runtime"""
    return (
        os.environ.get("SINCH_APP_KEY", ""),
        os.environ.get("SINCH_APP_SECRET", "")
    )

@router.post("/auth-token")
async def get_sinch_voice_auth_token(user=Depends(get_current_user)):
    """Generate Sinch Voice & Video SDK JWT token for authentication"""
    SINCH_APP_KEY, SINCH_APP_SECRET = get_sinch_voice_credentials()
    if not SINCH_APP_KEY or not SINCH_APP_SECRET:
        raise HTTPException(status_code=503, detail="Voice service not configured")
    
    try:
        sinch_voice_jwt = SinchVoiceJWTGenerator(SINCH_APP_KEY, SINCH_APP_SECRET)
        token = sinch_voice_jwt.generate_token(user["id"], ttl_seconds=3600)
        return {
            "token": token,
            "app_key": SINCH_APP_KEY,
            "environment_host": "ocra.api.sinch.com",
            "user_id": user["id"],
            "display_name": user.get("display_name", user.get("username", "")),
            "expires_in": 3600
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token generation failed: {str(e)}")

@router.get("/token")
async def get_voice_token(user=Depends(get_current_user)):
    """Get Sinch Voice JWT token for the user (legacy endpoint)."""
    return await get_sinch_voice_auth_token(user)

@router.get("/config")
async def get_voice_config(user=Depends(get_current_user)):
    """Get Sinch Voice SDK configuration."""
    SINCH_APP_KEY, _ = get_sinch_voice_credentials()
    return {
        "app_key": SINCH_APP_KEY,
        "user_id": user["id"],
        "display_name": user.get("display_name", user.get("username", "")),
        "environment": "production"
    }
