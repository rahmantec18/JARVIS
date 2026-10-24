from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# Health Check
class HealthResponse(BaseModel):
    status: str
    assistant_name: str
    version: str
    ai_provider: str
    ai_model: str
    ai_connected: bool
    database_connected: bool
    desktop_agent_connected: bool
    timestamp: datetime


# Chat & Conversation
class ChatMessageInput(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User prompt or voice transcript")
    conversation_id: Optional[str] = Field(default=None, description="Existing conversation ID if continuing")
    stream: bool = Field(default=False, description="Whether to stream response tokens")


class ToolCallDetail(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any]
    result: Optional[Any] = None
    status: str = "success"  # success, failed, awaiting_approval


class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    tool_calls: List[ToolCallDetail] = []
    status: str = "success"  # success, error, awaiting_approval
    suggested_actions: List[str] = []


class MessageSchema(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    tool_calls: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ConversationDetail(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageSchema] = []

    model_config = ConfigDict(from_attributes=True)


# Memory
class MemoryCreate(BaseModel):
    category: str = Field(default="general", description="preference, project, fact, general")
    key: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    approved: bool = True


class MemoryUpdate(BaseModel):
    category: Optional[str] = None
    key: Optional[str] = None
    content: Optional[str] = None
    approved: Optional[bool] = None


class MemoryResponse(BaseModel):
    id: str
    category: str
    key: str
    content: str
    approved: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Tasks
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = ""
    due_date: Optional[datetime] = None
    priority: str = Field(default="medium", description="low, medium, high, critical")


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None
    priority: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: str
    priority: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Tools
class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    requires_approval: bool = False
    connected: bool = True
    category: str = "general"


class ToolExecuteRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = {}


class ToolExecuteResponse(BaseModel):
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    requires_approval: bool = False
    approval_token: Optional[str] = None


# Desktop Agent
class DesktopStatusResponse(BaseModel):
    connected: bool
    service_url: str
    system_info: Optional[Dict[str, Any]] = None
    approved_apps: List[Dict[str, str]] = []
    allowed_directories: List[str] = []
    pending_approvals: int = 0


class DesktopActionRequest(BaseModel):
    action: str  # launch_app, open_url, system_info, read_file, create_note, notify
    parameters: Dict[str, Any] = {}
    confirmed: bool = False


class DesktopActionResponse(BaseModel):
    action: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    requires_confirmation: bool = False
    approval_id: Optional[str] = None


# Activity Log
class ActivityLogResponse(BaseModel):
    id: str
    action_type: str
    tool_name: Optional[str] = None
    summary: str
    status: str
    details: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
