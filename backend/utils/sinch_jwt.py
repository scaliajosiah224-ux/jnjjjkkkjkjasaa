"""Sinch Voice JWT Token Generator for authentication"""
import hmac
import hashlib
import time
import secrets
import base64
import json
from datetime import datetime, timezone

class SinchVoiceJWTGenerator:
    """Generate JWT tokens for Sinch Voice & Video SDK authentication"""
    def __init__(self, app_key: str, app_secret: str):
        self.app_key = app_key
        self.app_secret = app_secret
    
    def _derive_signing_key(self, date_str: str) -> bytes:
        """Derive signing key using HKDF"""
        salt = f"SinchRTCSigningKey{date_str}".encode()
        
        # HKDF-Extract
        hkdf_extract = hmac.new(
            salt,
            self.app_secret.encode(),
            hashlib.sha256
        ).digest()
        
        # HKDF-Expand
        hkdf_expand = hmac.new(
            hkdf_extract,
            b"SinchRTCSigningKey",
            hashlib.sha256
        ).digest()[:32]
        
        return hkdf_expand
    
    def generate_token(self, user_id: str, ttl_seconds: int = 3600) -> str:
        """Generate a JWT token for Sinch authentication"""
        now = int(time.time())
        expiry = now + ttl_seconds
        current_date = datetime.now(timezone.utc).strftime("%Y%m%d")
        
        header = {
            "alg": "HS256",
            "kid": f"hkdfv1-{current_date}"
        }
        
        payload = {
            "iss": f"//rtc.sinch.com/applications/{self.app_key}",
            "sub": f"//rtc.sinch.com/applications/{self.app_key}/users/{user_id}",
            "iat": now,
            "exp": expiry,
            "nonce": secrets.token_hex(16)
        }
        
        signing_key = self._derive_signing_key(current_date)
        
        # Encode header and payload
        header_encoded = base64.urlsafe_b64encode(
            json.dumps(header, separators=(',', ':')).encode()
        ).decode().rstrip('=')
        
        payload_encoded = base64.urlsafe_b64encode(
            json.dumps(payload, separators=(',', ':')).encode()
        ).decode().rstrip('=')
        
        # Create signature
        message = f"{header_encoded}.{payload_encoded}"
        signature = base64.urlsafe_b64encode(
            hmac.new(signing_key, message.encode(), hashlib.sha256).digest()
        ).decode().rstrip('=')
        
        return f"{message}.{signature}"
