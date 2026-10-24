import inspect
import json
from typing import Callable, Dict, Any, List, Optional
from pydantic import BaseModel
from app.models.schemas import ToolDefinition, ToolExecuteResponse


class ToolMetadata(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    func: Any
    requires_approval: bool = False
    category: str = "general"


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolMetadata] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        requires_approval: bool = False,
        category: str = "general"
    ):
        """Decorator or method to register a tool."""
        def decorator(func: Callable):
            self._tools[name] = ToolMetadata(
                name=name,
                description=description,
                parameters=parameters,
                func=func,
                requires_approval=requires_approval,
                category=category
            )
            return func
        return decorator

    def get_tool(self, name: str) -> Optional[ToolMetadata]:
        return self._tools.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name=tool.name,
                description=tool.description,
                parameters=tool.parameters,
                requires_approval=tool.requires_approval,
                connected=True,
                category=tool.category
            )
            for tool in self._tools.values()
        ]

    def get_openai_tool_specs(self) -> List[Dict[str, Any]]:
        """Return tool definitions in OpenAI function call format."""
        specs = []
        for tool in self._tools.values():
            specs.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            })
        return specs

    async def execute(self, name: str, arguments: Dict[str, Any], approved: bool = False) -> ToolExecuteResponse:
        tool = self.get_tool(name)
        if not tool:
            return ToolExecuteResponse(
                tool_name=name,
                success=False,
                result=None,
                error=f"Tool '{name}' is not registered."
            )

        if tool.requires_approval and not approved:
            return ToolExecuteResponse(
                tool_name=name,
                success=False,
                result=None,
                error=f"Tool '{name}' requires explicit user confirmation.",
                requires_approval=True
            )

        try:
            func = tool.func
            if inspect.iscoroutinefunction(func):
                result = await func(**arguments)
            else:
                result = func(**arguments)

            return ToolExecuteResponse(
                tool_name=name,
                success=True,
                result=result,
                error=None
            )
        except Exception as e:
            return ToolExecuteResponse(
                tool_name=name,
                success=False,
                result=None,
                error=f"Error executing '{name}': {str(e)}"
            )


tool_registry = ToolRegistry()
