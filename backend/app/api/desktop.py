import httpx
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.models.entities import ActivityLog
from app.models.schemas import (
    DesktopStatusResponse, DesktopActionRequest, DesktopActionResponse
)

router = APIRouter(prefix="/desktop", tags=["Desktop Agent"])


def get_desktop_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.DESKTOP_AGENT_TOKEN}",
        "Content-Type": "application/json"
    }


@router.get("/status", response_model=DesktopStatusResponse)
async def get_desktop_status():
    """Retrieve Windows Desktop Agent status, system metrics, and permissions."""
    if not settings.DESKTOP_AGENT_ENABLED:
        return DesktopStatusResponse(
            connected=False,
            service_url=settings.DESKTOP_AGENT_URL,
            system_info=None,
            approved_apps=[],
            allowed_directories=[],
            pending_approvals=0
        )

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(
                f"{settings.DESKTOP_AGENT_URL.rstrip('/')}/api/status",
                headers=get_desktop_headers()
            )
            if resp.status_code == 200:
                data = resp.json()
                return DesktopStatusResponse(
                    connected=True,
                    service_url=settings.DESKTOP_AGENT_URL,
                    system_info=data.get("system_info"),
                    approved_apps=data.get("approved_apps", []),
                    allowed_directories=data.get("allowed_directories", []),
                    pending_approvals=data.get("pending_approvals", 0)
                )
    except Exception:
        pass

    return DesktopStatusResponse(
        connected=False,
        service_url=settings.DESKTOP_AGENT_URL,
        system_info=None,
        approved_apps=[
            {"id": "notepad", "name": "Notepad", "description": "Text editor"},
            {"id": "calc", "name": "Calculator", "description": "Windows Calculator"},
            {"id": "explorer", "name": "File Explorer", "description": "Windows File Manager"},
            {"id": "code", "name": "VS Code", "description": "Visual Studio Code"},
            {"id": "cmd", "name": "Command Prompt", "description": "Windows Command Line (requires confirmation)"}
        ],
        allowed_directories=[],
        pending_approvals=0
    )


@router.post("/action", response_model=DesktopActionResponse)
async def execute_desktop_action(request: DesktopActionRequest, db: AsyncSession = Depends(get_db)):
    """Dispatch an action to the Windows Desktop Agent."""
    if not settings.DESKTOP_AGENT_ENABLED:
        raise HTTPException(status_code=400, detail="Desktop agent integration is disabled")

    url = f"{settings.DESKTOP_AGENT_URL.rstrip('/')}/api/action"
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(
                url,
                json=request.model_dump(),
                headers=get_desktop_headers()
            )
            data = resp.json()

            if "action" not in data:
                data["action"] = request.action

            # Record in audit log
            log = ActivityLog(
                action_type="desktop_action",
                tool_name=request.action,
                summary=f"Desktop action: {request.action}",
                status="success" if data.get("success") else ("awaiting_approval" if data.get("requires_confirmation") else "failed"),
                details=str(request.parameters)
            )
            db.add(log)
            await db.commit()

            return DesktopActionResponse(**data)
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Windows Desktop Agent is currently offline. Please start the desktop agent service."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to communicate with desktop agent: {str(e)}")


@router.post("/approve/{approval_id}")
async def approve_pending_action(approval_id: str, approved: bool = True):
    """Confirm or reject a sensitive desktop action awaiting approval."""
    url = f"{settings.DESKTOP_AGENT_URL.rstrip('/')}/api/approve/{approval_id}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                url,
                json={"approved": approved},
                headers=get_desktop_headers()
            )
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit approval: {str(e)}")
