from datetime import datetime, timezone
import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.config import settings
from app.core.database import get_db
from app.models.schemas import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
async def check_health(db: AsyncSession = Depends(get_db)):
    """Health check reporting subsystem status without exposing credentials."""
    # Check Database
    db_connected = False
    try:
        await db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False

    # Check Desktop Agent
    desktop_agent_connected = False
    if settings.DESKTOP_AGENT_ENABLED:
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                res = await client.get(f"{settings.DESKTOP_AGENT_URL.rstrip('/')}/health")
                if res.status_code == 200:
                    desktop_agent_connected = True
        except Exception:
            desktop_agent_connected = False

    ai_connected = bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip())

    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        assistant_name=settings.ASSISTANT_NAME,
        version="1.0.0",
        ai_provider=settings.AI_PROVIDER,
        ai_model=settings.AI_MODEL,
        ai_connected=ai_connected,
        database_connected=db_connected,
        desktop_agent_connected=desktop_agent_connected,
        timestamp=datetime.now(timezone.utc)
    )
