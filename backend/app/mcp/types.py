"""
MCP Type Definitions
"""
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MCPTransport(str, Enum):
    """MCP Server transport type"""
    STDIO = "stdio"
    HTTP = "http"


class MCPCapability(str, Enum):
    """MCP Server capabilities"""
    TOOLS = "tools"
    RESOURCES = "resources"
    PROMPTS = "prompts"


class MCPTool(BaseModel):
    """MCP Tool definition"""
    name: str = Field(..., description="Tool name (prefixed with server name)")
    description: str = Field(..., description="Tool description")
    input_schema: dict[str, Any] = Field(..., description="JSON Schema for tool input")
    server_name: str = Field(..., description="Name of the MCP server providing this tool")

    model_config = ConfigDict(frozen=True)


class MCPToolResult(BaseModel):
    """Result from MCP tool execution"""
    success: bool = Field(..., description="Whether the tool execution succeeded")
    content: Any = Field(None, description="Tool output content")
    error: str | None = Field(None, description="Error message if failed")
    duration_ms: float | None = Field(None, description="Execution duration in milliseconds")

    @classmethod
    def from_success(cls, content: Any, duration_ms: float = 0) -> "MCPToolResult":
        """Create a successful result"""
        return cls(success=True, content=content, duration_ms=duration_ms)

    @classmethod
    def from_error(cls, error: str, duration_ms: float = 0) -> "MCPToolResult":
        """Create an error result"""
        return cls(success=False, error=error, duration_ms=duration_ms)


class MCPResourceContent(BaseModel):
    """MCP Resource content"""
    uri: str
    mime_type: str | None = None
    text: str | None = None
    blob: bytes | None = None


class MCPPrompt(BaseModel):
    """MCP Prompt definition"""
    name: str
    description: str | None = None
    arguments: list[dict[str, Any]] | None = None
