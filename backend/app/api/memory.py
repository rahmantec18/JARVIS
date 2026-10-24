from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, desc
from app.core.database import get_db
from app.models.entities import MemoryItem, ActivityLog
from app.models.schemas import MemoryCreate, MemoryUpdate, MemoryResponse

router = APIRouter(prefix="/memory", tags=["Memory"])


@router.get("", response_model=List[MemoryResponse])
async def list_memories(
    category: Optional[str] = Query(None, description="Filter by category: preference, project, fact, general"),
    query: Optional[str] = Query(None, description="Search query string"),
    db: AsyncSession = Depends(get_db)
):
    """List persistent memories with optional filtering and search."""
    stmt = select(MemoryItem).order_by(desc(MemoryItem.created_at))
    if category:
        stmt = stmt.where(MemoryItem.category == category)

    result = await db.execute(stmt)
    memories = result.scalars().all()

    if query:
        q_lower = query.lower()
        memories = [m for m in memories if q_lower in m.key.lower() or q_lower in m.content.lower()]

    return [MemoryResponse.model_validate(m) for m in memories]


@router.post("", response_model=MemoryResponse)
async def create_memory(memory_in: MemoryCreate, db: AsyncSession = Depends(get_db)):
    """Save an approved fact, preference, or project context."""
    # Check for existing key in the same category
    existing = await db.execute(
        select(MemoryItem).where(MemoryItem.key == memory_in.key, MemoryItem.category == memory_in.category)
    )
    item = existing.scalar_one_or_none()
    if item:
        item.content = memory_in.content
        item.approved = memory_in.approved
        item.updated_at = datetime.now(timezone.utc)
    else:
        item = MemoryItem(
            category=memory_in.category,
            key=memory_in.key,
            content=memory_in.content,
            approved=memory_in.approved
        )
        db.add(item)

    # Log memory addition
    log = ActivityLog(
        action_type="memory_update",
        summary=f"Memory updated: [{memory_in.category}] {memory_in.key}",
        status="success"
    )
    db.add(log)

    await db.commit()
    await db.refresh(item)
    return MemoryResponse.model_validate(item)


@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(memory_id: str, memory_update: MemoryUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing memory item."""
    result = await db.execute(select(MemoryItem).where(MemoryItem.id == memory_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Memory item not found")

    if memory_update.category is not None:
        item.category = memory_update.category
    if memory_update.key is not None:
        item.key = memory_update.key
    if memory_update.content is not None:
        item.content = memory_update.content
    if memory_update.approved is not None:
        item.approved = memory_update.approved

    item.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(item)
    return MemoryResponse.model_validate(item)


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a memory item."""
    result = await db.execute(select(MemoryItem).where(MemoryItem.id == memory_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Memory item not found")

    await db.delete(item)
    await db.commit()
    return {"status": "success", "message": f"Memory item '{item.key}' deleted"}


@router.delete("")
async def clear_all_memories(db: AsyncSession = Depends(get_db)):
    """Purge all persistent memories."""
    await db.execute(delete(MemoryItem))
    log = ActivityLog(
        action_type="memory_wipe",
        summary="All memory banks purged by user command",
        status="success"
    )
    db.add(log)
    await db.commit()
    return {"status": "success", "message": "All memory records cleared"}
