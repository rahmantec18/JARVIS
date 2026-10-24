from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.entities import ActivityLog
from app.models.schemas import ActivityLogResponse

router = APIRouter(prefix="/activity", tags=["Activity Log"])


@router.get("", response_model=List[ActivityLogResponse])
async def get_activity_log(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Retrieve recent assistant activity, tool executions, and state changes."""
    result = await db.execute(
        select(ActivityLog).order_by(desc(ActivityLog.created_at)).limit(limit)
    )
    logs = result.scalars().all()
    return [ActivityLogResponse.model_validate(l) for l in logs]
