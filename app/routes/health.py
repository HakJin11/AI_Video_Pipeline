import httpx
from fastapi import APIRouter

from app.config import COMFYUI_URL, OLLAMA_URL

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health():
    comfy_ok = False
    ollama_ok = False
    try:
        r = httpx.get(f"{COMFYUI_URL}/system_stats", timeout=3.0)
        comfy_ok = r.status_code == 200
    except httpx.HTTPError:
        pass
    try:
        r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=3.0)
        ollama_ok = r.status_code == 200
    except httpx.HTTPError:
        pass
    return {"comfyui": comfy_ok, "ollama": ollama_ok}
