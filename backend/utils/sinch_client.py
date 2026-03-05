"""Sinch API client helpers"""
import httpx
import os

SINCH_ACCESS_KEY_ID = os.environ.get("SINCH_ACCESS_KEY_ID", "")
SINCH_KEY_SECRET = os.environ.get("SINCH_KEY_SECRET", "")
SINCH_SMS_API_TOKEN = os.environ.get("SINCH_SMS_API_TOKEN", "")

async def get_sinch_access_token() -> str:
    """Get OAuth2 access token from Sinch using key ID and secret."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://auth.sinch.com/oauth2/token",
                data={"grant_type": "client_credentials"},
                auth=(SINCH_ACCESS_KEY_ID, SINCH_KEY_SECRET),
                timeout=10.0
            )
            resp.raise_for_status()
            return resp.json().get("access_token", "")
    except Exception as e:
        print(f"Sinch OAuth error: {e}")
        return ""

async def sinch_request(method: str, url: str, json_data: dict = None, use_token_auth: bool = True) -> dict:
    """Make authenticated request to Sinch API."""
    try:
        if use_token_auth:
            # Use API token directly (for SMS API)
            headers = {
                "Authorization": f"Bearer {SINCH_SMS_API_TOKEN}",
                "Content-Type": "application/json"
            }
        else:
            # Use OAuth2 access token (for Numbers API)
            token = await get_sinch_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        
        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                resp = await client.get(url, headers=headers, timeout=15.0)
            elif method.upper() == "POST":
                resp = await client.post(url, headers=headers, json=json_data, timeout=15.0)
            elif method.upper() == "DELETE":
                resp = await client.delete(url, headers=headers, timeout=15.0)
            else:
                resp = await client.request(method, url, headers=headers, json=json_data, timeout=15.0)
            
            if resp.status_code not in [200, 201]:
                print(f"Sinch API error {resp.status_code}: {resp.text}")
                return {"error": resp.text, "status_code": resp.status_code}
            
            return resp.json()
    except Exception as e:
        print(f"Sinch request error: {e}")
        return {"error": str(e)}
