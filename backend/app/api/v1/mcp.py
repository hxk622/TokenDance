"""
MCP API Endpoints

Provides REST API for MCP tool management and execution.
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.mcp import get_manager, MCPTool, MCPToolResult
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class ToolCallRequest(BaseModel):
    """Request to call a tool"""
    name: str = Field(..., description="Tool name")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")


class ToolCallResponse(BaseModel):
    """Response from tool call"""
    success: bool
    content: Any = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None


class ToolInfo(BaseModel):
    """Tool information"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str


class ServerInfo(BaseModel):
    """Server information"""
    name: str
    connected: bool
    tools_count: int


@router.get("/tools", response_model=List[ToolInfo])
async def list_tools():
    """
    List all available MCP tools.
    
    Returns tools from all connected MCP servers.
    """
    manager = get_manager()
    
    # Auto-start if not started
    if not manager.connected_servers:
        await manager.start()
    
    tools = manager.get_tools()
    return [
        ToolInfo(
            name=t.name,
            description=t.description,
            input_schema=t.input_schema,
            server_name=t.server_name,
        )
        for t in tools
    ]


@router.get("/tools/claude-format")
async def get_tools_claude_format():
    """
    Get tools in Claude API format.
    
    Ready to use with Anthropic's tool_use feature.
    """
    manager = get_manager()
    
    if not manager.connected_servers:
        await manager.start()
    
    return manager.get_tools_for_claude()


@router.post("/tools/call", response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest):
    """
    Execute a tool by name.
    
    Routes the call to the appropriate MCP server.
    """
    manager = get_manager()
    
    if not manager.connected_servers:
        await manager.start()
    
    tool = manager.get_tool(request.name)
    if not tool:
        raise HTTPException(
            status_code=404,
            detail=f"Tool not found: {request.name}"
        )
    
    logger.info(
        "mcp_api_tool_call",
        tool=request.name,
        arguments=request.arguments,
    )
    
    result = await manager.call_tool(request.name, request.arguments)
    
    return ToolCallResponse(
        success=result.success,
        content=result.content,
        error=result.error,
        duration_ms=result.duration_ms,
    )


@router.get("/servers", response_model=List[ServerInfo])
async def list_servers():
    """
    List MCP server status.
    """
    manager = get_manager()
    
    # Get all registered servers
    from app.mcp import get_registry
    registry = get_registry()
    
    servers = []
    for config in registry.list_enabled():
        connected = config.name in manager.connected_servers
        tools_count = len([
            t for t in manager.get_tools()
            if t.server_name == config.name
        ]) if connected else 0
        
        servers.append(ServerInfo(
            name=config.name,
            connected=connected,
            tools_count=tools_count,
        ))
    
    return servers


@router.post("/servers/{server_name}/connect")
async def connect_server(server_name: str):
    """
    Connect to a specific MCP server.
    """
    manager = get_manager()
    success = await manager.connect(server_name)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to server: {server_name}"
        )
    
    # Discover tools after connecting
    await manager.discover_tools()
    
    return {"status": "connected", "server": server_name}


@router.post("/servers/{server_name}/disconnect")
async def disconnect_server(server_name: str):
    """
    Disconnect from a specific MCP server.
    """
    manager = get_manager()
    await manager.disconnect(server_name)
    
    return {"status": "disconnected", "server": server_name}


@router.post("/start")
async def start_mcp():
    """
    Start all auto-start MCP servers.
    """
    manager = get_manager()
    await manager.start()
    
    return {
        "status": "started",
        "connected_servers": manager.connected_servers,
        "tools_count": len(manager.get_tools()),
    }


@router.post("/stop")
async def stop_mcp():
    """
    Stop all MCP server connections.
    """
    manager = get_manager()
    await manager.stop()
    
    return {"status": "stopped"}
