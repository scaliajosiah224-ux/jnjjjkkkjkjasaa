"""GIF search routes"""
from fastapi import APIRouter, Depends
import httpx
import os

from routes.dependencies import get_current_user

router = APIRouter(prefix="/api/gifs", tags=["gifs"])

@router.get("/search")
async def search_gifs(q: str = "trending", limit: int = 20, user=Depends(get_current_user)):
    """Search GIFs via Klipy API."""
    # Load API key at runtime, not at import time
    KLIPY_API_KEY = os.environ.get("KLIPY_API_KEY", "")
    
    if not KLIPY_API_KEY:
        return {"gifs": [], "error": "Klipy API key not configured"}
    
    try:
        async with httpx.AsyncClient() as client:
            base_url = f"https://api.klipy.com/api/v1/{KLIPY_API_KEY}/gifs"
            per_page = min(limit, 50)
            
            if q == "trending":
                url = f"{base_url}/trending?per_page={per_page}&locale=en-US"
            else:
                url = f"{base_url}/search?q={q}&per_page={per_page}&locale=en-US"
            
            resp = await client.get(url, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                gifs = []
                
                gif_data = data.get("data", {}).get("data", [])
                
                for result in gif_data:
                    hd_gif = result.get("file", {}).get("hd", {}).get("gif", {})
                    sd_gif = result.get("file", {}).get("sd", {}).get("gif", {})
                    
                    gif_url = hd_gif.get("url") or sd_gif.get("url")
                    
                    if gif_url:
                        gifs.append({
                            "id": result.get("slug", result.get("id")),
                            "url": gif_url,
                            "preview": sd_gif.get("url", gif_url),
                            "width": hd_gif.get("width", sd_gif.get("width", 200)),
                            "height": hd_gif.get("height", sd_gif.get("height", 200)),
                            "title": result.get("title", "")
                        })
                return {"gifs": gifs}
            else:
                return {"gifs": [], "error": f"Klipy API error: {resp.status_code}"}
    except Exception as e:
        return {"gifs": [], "error": str(e)}
