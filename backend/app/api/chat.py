import json
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, desc
from app.core.database import get_db
from app.models.entities import Conversation, Message, MemoryItem, ActivityLog
from app.models.schemas import (
    ChatRequest, ChatResponse, ConversationSummary,
    ConversationDetail, MessageSchema, ToolCallDetail
)
from app.ai.provider import get_ai_provider, check_fast_path_action

router = APIRouter(prefix="", tags=["Chat & Conversations"])


@router.post("/chat", response_model=ChatResponse)
async def send_chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Process a conversational request with memory retrieval and tool execution."""
    conversation_id = request.conversation_id

    # -------------------------------------------------------------
    # 0. ZERO-LATENCY FAST-PATH REFLEX ROUTER (< 15ms)
    # Direct execution of desktop actions, WhatsApp, Chrome, volume, screenshot, lock, time, etc.
    # -------------------------------------------------------------
    fast_response = await check_fast_path_action(request.message)
    if fast_response:
        # Find or create conversation
        if conversation_id:
            conv_query = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
            conversation = conv_query.scalar_one_or_none()
            if not conversation:
                conversation = Conversation(id=conversation_id, title=request.message[:40])
                db.add(conversation)
        else:
            conversation = Conversation(title=request.message[:40])
            db.add(conversation)
            await db.flush()
            conversation_id = conversation.id

        user_msg = Message(
            conversation_id=conversation_id,
            role="user",
            content=request.message
        )
        asst_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=fast_response.message,
            tool_calls=json.dumps([t.model_dump() for t in fast_response.tool_calls]) if fast_response.tool_calls else None
        )
        db.add(user_msg)
        db.add(asst_msg)

        activity = ActivityLog(
            action_type="fast_path",
            tool_name=fast_response.tool_calls[0].name if fast_response.tool_calls else "direct_action",
            summary=f"Directive: '{request.message[:35]}' executed instantly",
            status="success",
            details=json.dumps({"fast_path": True, "tools": [t.name for t in fast_response.tool_calls]})
        )
        db.add(activity)
        conversation.updated_at = datetime.now(timezone.utc)
        await db.commit()

        fast_response.conversation_id = conversation_id
        return fast_response

    # Find or create conversation for general reasoning
    if conversation_id:
        conv_query = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
        conversation = conv_query.scalar_one_or_none()
        if not conversation:
            conversation = Conversation(id=conversation_id, title=request.message[:40])
            db.add(conversation)
    else:
        conversation = Conversation(title=request.message[:40])
        db.add(conversation)
        await db.flush()
        conversation_id = conversation.id

    # Save user message
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=request.message
    )
    db.add(user_msg)

    # Load persistent approved memories
    mem_query = await db.execute(select(MemoryItem).where(MemoryItem.approved == True))
    memory_records = mem_query.scalars().all()
    memory_strings = [f"[{m.category.upper()}] {m.key}: {m.content}" for m in memory_records]

    # Load previous messages for context (last 15 messages)
    history_query = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(15)
    )
    history_messages = list(reversed(history_query.scalars().all()))
    message_dicts = [{"role": m.role, "content": m.content} for m in history_messages]
    # Add the current user prompt if not already in message_dicts
    if not message_dicts or message_dicts[-1]["content"] != request.message:
        message_dicts.append({"role": "user", "content": request.message})

    # Call AI Provider
    provider = get_ai_provider()
    try:
        response = await provider.chat(messages=message_dicts, memories=memory_strings)
    except Exception as e:
        # Fallback error response
        response = ChatResponse(
            conversation_id=conversation_id,
            message=f"I encountered a temporary disruption while processing: {str(e)}",
            tool_calls=[],
            status="error"
        )

    response.conversation_id = conversation_id

    # Save assistant message
    asst_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=response.message,
        tool_calls=json.dumps([t.model_dump() for t in response.tool_calls]) if response.tool_calls else None
    )
    db.add(asst_msg)

    # Log activity
    log_summary = f"Prompt: '{request.message[:35]}...' -> Response generated"
    if response.tool_calls:
        log_summary += f" ({len(response.tool_calls)} tools invoked)"
    activity = ActivityLog(
        action_type="chat",
        tool_name=response.tool_calls[0].name if response.tool_calls else None,
        summary=log_summary,
        status="awaiting_approval" if response.status == "awaiting_approval" else "success",
        details=json.dumps({"tools": [t.name for t in response.tool_calls]})
    )
    db.add(activity)

    conversation.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return response


@router.post("/chat/stream")
async def stream_chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Stream chat response tokens using Server-Sent Events."""
    provider = get_ai_provider()
    messages = [{"role": "user", "content": request.message}]

    # Load memories
    mem_query = await db.execute(select(MemoryItem).where(MemoryItem.approved == True))
    memory_records = mem_query.scalars().all()
    memory_strings = [f"[{m.category.upper()}] {m.key}: {m.content}" for m in memory_records]

    async def event_generator():
        try:
            async for chunk in provider.stream_chat(messages, memory_strings):
                yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations(limit: int = 30, db: AsyncSession = Depends(get_db)):
    """List recent conversations."""
    result = await db.execute(
        select(Conversation).order_by(desc(Conversation.updated_at)).limit(limit)
    )
    conversations = result.scalars().all()
    summaries = []
    for conv in conversations:
        # Count messages
        msg_count_res = await db.execute(
            select(Message).where(Message.conversation_id == conv.id)
        )
        msg_count = len(msg_count_res.scalars().all())
        summaries.append(ConversationSummary(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=msg_count
        ))
    return summaries


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id: str, db: AsyncSession = Depends(get_db)):
    """Get full conversation details with ordered messages."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg_result = await db.execute(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())
    )
    messages = msg_result.scalars().all()

    return ConversationDetail(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[MessageSchema.model_validate(m) for m in messages]
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a conversation and its messages."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.execute(delete(Conversation).where(Conversation.id == conversation_id))
    await db.commit()
    return {"status": "success", "message": "Conversation removed"}
