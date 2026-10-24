from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from app.core.config import settings

router = APIRouter(prefix="/settings", tags=["Settings"])


class SafeSettingsResponse(BaseModel):
    assistant_name: str
    assistant_voice: str
    ai_provider: str
    ai_model: str
    has_openai_key: bool
    masked_key: str
    has_gemini_key: bool
    masked_gemini_key: str
    openai_base_url: Optional[str] = None
    desktop_agent_enabled: bool
    desktop_agent_url: str
    has_desktop_token: bool
    search_provider: str
    authorized_user: str
    biometric_enforcement: bool


class SettingsUpdateRequest(BaseModel):
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    gemini_api_key: Optional[str] = None
    assistant_voice: Optional[str] = None
    desktop_agent_enabled: Optional[bool] = None
    desktop_agent_url: Optional[str] = None
    desktop_agent_token: Optional[str] = None
    authorized_user: Optional[str] = None
    biometric_enforcement: Optional[bool] = None


def _persist_to_env():
    env_path = Path(__file__).parent.parent.parent / ".env"
    lines = [
        f"AI_PROVIDER={settings.AI_PROVIDER}",
        f"AI_MODEL={settings.AI_MODEL}",
        f"OPENAI_API_KEY={settings.OPENAI_API_KEY}",
        f"OPENAI_BASE_URL={settings.OPENAI_BASE_URL}",
        f"GEMINI_API_KEY={settings.GEMINI_API_KEY}",
        f"AUTHORIZED_USER={settings.AUTHORIZED_USER}",
        f"BIOMETRIC_ENFORCEMENT={str(settings.BIOMETRIC_ENFORCEMENT).lower()}",
        f"BACKEND_HOST={settings.BACKEND_HOST}",
        f"BACKEND_PORT={settings.BACKEND_PORT}",
        f"DATABASE_URL={settings.DATABASE_URL}",
        f"DESKTOP_AGENT_ENABLED={str(settings.DESKTOP_AGENT_ENABLED).lower()}",
        f"DESKTOP_AGENT_URL={settings.DESKTOP_AGENT_URL}",
        f"DESKTOP_AGENT_TOKEN={settings.DESKTOP_AGENT_TOKEN}",
        f"SEARCH_PROVIDER={settings.SEARCH_PROVIDER}",
    ]
    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except Exception:
        pass


@router.get("", response_model=SafeSettingsResponse)
async def get_settings():
    """Retrieve runtime settings without exposing raw secrets."""
    has_key = bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip())
    masked = ""
    if has_key:
        raw = settings.OPENAI_API_KEY.strip()
        masked = f"{raw[:4]}...{raw[-4:]}" if len(raw) > 8 else "****"

    has_gemini = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())
    masked_gemini = ""
    if has_gemini:
        raw_g = settings.GEMINI_API_KEY.strip()
        masked_gemini = f"{raw_g[:4]}...{raw_g[-4:]}" if len(raw_g) > 8 else "****"

    return SafeSettingsResponse(
        assistant_name=settings.ASSISTANT_NAME,
        assistant_voice=settings.ASSISTANT_VOICE,
        ai_provider=settings.AI_PROVIDER,
        ai_model=settings.AI_MODEL,
        has_openai_key=has_key,
        masked_key=masked,
        has_gemini_key=has_gemini,
        masked_gemini_key=masked_gemini,
        openai_base_url=settings.OPENAI_BASE_URL,
        desktop_agent_enabled=settings.DESKTOP_AGENT_ENABLED,
        desktop_agent_url=settings.DESKTOP_AGENT_URL,
        has_desktop_token=bool(settings.DESKTOP_AGENT_TOKEN),
        search_provider=settings.SEARCH_PROVIDER,
        authorized_user=settings.AUTHORIZED_USER,
        biometric_enforcement=settings.BIOMETRIC_ENFORCEMENT
    )


@router.post("", response_model=SafeSettingsResponse)
async def update_settings(update: SettingsUpdateRequest):
    """Update runtime settings."""
    if update.ai_provider is not None:
        settings.AI_PROVIDER = update.ai_provider
    if update.ai_model is not None:
        settings.AI_MODEL = update.ai_model
    if update.openai_api_key is not None and update.openai_api_key.strip():
        settings.OPENAI_API_KEY = update.openai_api_key.strip()
    if update.gemini_api_key is not None and update.gemini_api_key.strip():
        settings.GEMINI_API_KEY = update.gemini_api_key.strip()
    if update.openai_base_url is not None:
        settings.OPENAI_BASE_URL = update.openai_base_url.strip()
    if update.assistant_voice is not None:
        settings.ASSISTANT_VOICE = update.assistant_voice
    if update.desktop_agent_enabled is not None:
        settings.DESKTOP_AGENT_ENABLED = update.desktop_agent_enabled
    if update.desktop_agent_url is not None:
        settings.DESKTOP_AGENT_URL = update.desktop_agent_url
    if update.desktop_agent_token is not None and update.desktop_agent_token.strip():
        settings.DESKTOP_AGENT_TOKEN = update.desktop_agent_token.strip()
    if update.authorized_user is not None:
        settings.AUTHORIZED_USER = update.authorized_user.strip()
    if update.biometric_enforcement is not None:
        settings.BIOMETRIC_ENFORCEMENT = update.biometric_enforcement

    _persist_to_env()
    return await get_settings()


@router.post("/test-gemini")
async def test_gemini_connection(payload: Optional[Dict[str, str]] = None):
    """Backend-only connection test for Google Gemini API."""
    import httpx
    api_key = (payload.get("key") if payload else None) or settings.GEMINI_API_KEY
    if not api_key or not api_key.strip():
        return {
            "online": False,
            "status": "unconfigured",
            "message": "Gemini API key is not configured in backend environment."
        }

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key.strip()}"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name", "").replace("models/", "") for m in data.get("models", [])[:5]]
                return {
                    "online": True,
                    "status": "connected",
                    "provider": "Google Gemini",
                    "available_models": models,
                    "message": "Google Gemini API connection established successfully."
                }
            else:
                return {
                    "online": False,
                    "status": "error",
                    "code": resp.status_code,
                    "message": f"Google Gemini returned HTTP {resp.status_code}: {resp.text[:200]}"
                }
    except Exception as e:
        return {
            "online": False,
            "status": "error",
            "message": f"Gemini connection failed: {str(e)}"
        }

