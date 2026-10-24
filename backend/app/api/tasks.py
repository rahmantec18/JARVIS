from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, desc
from app.core.database import get_db
from app.models.entities import TaskItem, ActivityLog
from app.models.schemas import TaskCreate, TaskUpdate, TaskResponse

router = APIRouter(prefix="/tasks", tags=["Tasks & Reminders"])


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    status: Optional[str] = Query(None, description="Filter by status: pending, in_progress, completed"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve scheduled tasks and reminders."""
    stmt = select(TaskItem).order_by(desc(TaskItem.created_at))
    if status:
        stmt = stmt.where(TaskItem.status == status)

    result = await db.execute(stmt)
    tasks = result.scalars().all()
    return [TaskResponse.model_validate(t) for t in tasks]


@router.post("", response_model=TaskResponse)
async def create_task(task_in: TaskCreate, db: AsyncSession = Depends(get_db)):
    """Create a persistent task or reminder."""
    task = TaskItem(
        title=task_in.title,
        description=task_in.description or "",
        due_date=task_in.due_date,
        priority=task_in.priority,
        status="pending"
    )
    db.add(task)

    log = ActivityLog(
        action_type="task_create",
        summary=f"Task logged: {task_in.title} [{task_in.priority}]",
        status="success"
    )
    db.add(log)

    await db.commit()
    await db.refresh(task)
    return TaskResponse.model_validate(task)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, task_up: TaskUpdate, db: AsyncSession = Depends(get_db)):
    """Update task status, due date, or priority."""
    result = await db.execute(select(TaskItem).where(TaskItem.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_up.title is not None:
        task.title = task_up.title
    if task_up.description is not None:
        task.description = task_up.description
    if task_up.due_date is not None:
        task.due_date = task_up.due_date
    if task_up.priority is not None:
        task.priority = task_up.priority
    if task_up.status is not None:
        task.status = task_up.status
        if task_up.status == "completed" and not task.completed_at:
            task.completed_at = datetime.now(timezone.utc)
        elif task_up.status != "completed":
            task.completed_at = None

    await db.commit()
    await db.refresh(task)
    return TaskResponse.model_validate(task)


@router.delete("/{task_id}")
async def delete_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """Remove a task."""
    result = await db.execute(select(TaskItem).where(TaskItem.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await db.delete(task)
    await db.commit()
    return {"status": "success", "message": f"Task '{task.title}' removed"}
