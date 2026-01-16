"""
MCP Type Definitions
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from enum import Enum


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
    input_schema: Dict[str, Any] = Field(..., description="JSON Schema for tool input")
    server_name: str = Field(..., description="Name of the MCP server providing this tool")
    
    model_config = ConfigDict(frozen=True)


class MCPToolResult(BaseModel):
    """Result from MCP tool execution"""
    success: bool = Field(..., description="Whether the tool execution succeeded")
    content: Any = Field(None, description="Tool output content")
    error: Optional[str] = Field(None, description="Error message if failed")
    duration_ms: Optional[float] = Field(None, description="Execution duration in milliseconds")
    
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
    mime_type: Optional[str] = None
    text: Optional[str] = None
    blob: Optional[bytes] = None


class MCPPrompt(BaseModel):
    """MCP Prompt definition"""
    name: str
    description: Optional[str] = None
    arguments: Optional[List[Dict[str, Any]]] = None
