import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.entities import ActivityLog
from app.models.schemas import ToolDefinition, ToolExecuteRequest, ToolExecuteResponse
from app.tools.registry import tool_registry

router = APIRouter(prefix="/tools", tags=["Tools"])


@router.get("", response_model=List[ToolDefinition])
async def list_available_tools():
    """List all registered system tools, their parameters, and status."""
    return tool_registry.list_tools()


@router.post("/execute", response_model=ToolExecuteResponse)
async def execute_tool(request: ToolExecuteRequest, db: AsyncSession = Depends(get_db)):
    """Execute a registered tool directly with provided arguments."""
    tool = tool_registry.get_tool(request.tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{request.tool_name}' not found")

    result = await tool_registry.execute(request.tool_name, request.arguments)

    # Log tool execution
    log = ActivityLog(
        action_type="tool_execution",
        tool_name=request.tool_name,
        summary=f"Executed tool: {request.tool_name}",
        status="success" if result.success else ("awaiting_approval" if result.requires_approval else "failed"),
        details=json.dumps({"arguments": request.arguments, "error": result.error})
    )
    db.add(log)
    await db.commit()

    return result
