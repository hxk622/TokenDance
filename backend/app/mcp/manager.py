"""
MCP Manager

Central manager for MCP server connections and tool execution.
"""
import asyncio
import time
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from app.mcp.registry import MCPServerRegistry, MCPServerConfig, get_registry
from app.mcp.types import MCPTool, MCPToolResult, MCPCapability
from app.core.logging import get_logger

logger = get_logger(__name__)


class MCPServerConnection:
    """
    Represents a connection to an MCP server.
    
    In a full implementation, this would use the MCP SDK.
    For now, we provide a mock implementation that demonstrates the interface.
    """
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.name = config.name
        self._connected = False
        self._tools: List[MCPTool] = []
        self._process = None
    
    async def connect(self) -> bool:
        """Establish connection to the MCP server"""
        if self._connected:
            return True
        
        try:
            # TODO: Implement actual MCP connection using mcp SDK
            # For now, simulate connection
            logger.info(f"Connecting to MCP server: {self.name}")
            
            # In real implementation:
            # self._process = await asyncio.create_subprocess_exec(
            #     self.config.command,
            #     *self.config.args,
            #     stdin=asyncio.subprocess.PIPE,
            #     stdout=asyncio.subprocess.PIPE,
            #     stderr=asyncio.subprocess.PIPE,
            #     env={**os.environ, **self.config.env},
            # )
            # 
            # Then use MCP SDK to initialize session
            
            # Mock: simulate connection delay
            await asyncio.sleep(0.1)
            
            self._connected = True
            self._load_mock_tools()
            
            logger.info(
                f"mcp_server_connected",
                server=self.name,
                tools_count=len(self._tools),
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {self.name}: {e}")
            return False
    
    def _load_mock_tools(self):
        """Load mock tools for demonstration"""
        if self.name == "filesystem":
            self._tools = [
                MCPTool(
                    name="filesystem_read_file",
                    description="Read contents of a file",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path"}
                        },
                        "required": ["path"]
                    },
                    server_name=self.name,
                ),
                MCPTool(
                    name="filesystem_write_file",
                    description="Write contents to a file",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path"},
                            "content": {"type": "string", "description": "Content to write"}
                        },
                        "required": ["path", "content"]
                    },
                    server_name=self.name,
                ),
                MCPTool(
                    name="filesystem_list_directory",
                    description="List contents of a directory",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Directory path"}
                        },
                        "required": ["path"]
                    },
                    server_name=self.name,
                ),
            ]
        elif self.name == "web-search":
            self._tools = [
                MCPTool(
                    name="web-search_brave_search",
                    description="Search the web using Brave Search",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"}
                        },
                        "required": ["query"]
                    },
                    server_name=self.name,
                ),
            ]
        elif self.name == "memory":
            self._tools = [
                MCPTool(
                    name="memory_store",
                    description="Store a value in memory",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "key": {"type": "string"},
                            "value": {"type": "string"}
                        },
                        "required": ["key", "value"]
                    },
                    server_name=self.name,
                ),
                MCPTool(
                    name="memory_retrieve",
                    description="Retrieve a value from memory",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "key": {"type": "string"}
                        },
                        "required": ["key"]
                    },
                    server_name=self.name,
                ),
            ]
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        if not self._connected:
            return
        
        try:
            if self._process:
                self._process.terminate()
                await self._process.wait()
            
            self._connected = False
            self._tools = []
            logger.info(f"mcp_server_disconnected", server=self.name)
            
        except Exception as e:
            logger.error(f"Error disconnecting from {self.name}: {e}")
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    def get_tools(self) -> List[MCPTool]:
        """Get list of tools provided by this server"""
        return self._tools
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPToolResult:
        """Execute a tool on this server"""
        if not self._connected:
            return MCPToolResult.from_error("Server not connected")
        
        start_time = time.time()
        
        try:
            # TODO: Implement actual MCP tool call
            # For now, return mock results
            logger.info(
                "mcp_tool_call",
                server=self.name,
                tool=tool_name,
                arguments=arguments,
            )
            
            # Simulate tool execution
            await asyncio.sleep(0.05)
            
            # Mock responses based on tool
            if tool_name == "filesystem_read_file":
                content = f"# Mock content of {arguments.get('path', 'unknown')}\n\nThis is mock file content."
                result = MCPToolResult.from_success(content, duration_ms=(time.time() - start_time) * 1000)
            elif tool_name == "filesystem_write_file":
                result = MCPToolResult.from_success({"written": True, "path": arguments.get("path")}, duration_ms=(time.time() - start_time) * 1000)
            elif tool_name == "filesystem_list_directory":
                result = MCPToolResult.from_success(["file1.txt", "file2.md", "subdir/"], duration_ms=(time.time() - start_time) * 1000)
            elif tool_name == "web-search_brave_search":
                result = MCPToolResult.from_success({
                    "results": [
                        {"title": "Result 1", "url": "https://example.com/1"},
                        {"title": "Result 2", "url": "https://example.com/2"},
                    ]
                }, duration_ms=(time.time() - start_time) * 1000)
            else:
                result = MCPToolResult.from_success({"status": "ok"}, duration_ms=(time.time() - start_time) * 1000)
            
            logger.info(
                "mcp_tool_result",
                server=self.name,
                tool=tool_name,
                success=result.success,
                duration_ms=result.duration_ms,
            )
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Tool execution failed: {e}")
            return MCPToolResult.from_error(str(e), duration_ms=duration_ms)


class MCPManager:
    """
    Central manager for MCP server connections.
    
    Handles:
    - Server lifecycle (connect/disconnect)
    - Tool discovery and routing
    - Connection pooling
    """
    
    def __init__(self, registry: Optional[MCPServerRegistry] = None):
        self.registry = registry or get_registry()
        self._connections: Dict[str, MCPServerConnection] = {}
        self._tools_cache: Dict[str, MCPTool] = {}
        self._lock = asyncio.Lock()
    
    async def start(self, server_names: Optional[List[str]] = None):
        """
        Start MCP servers.
        
        If server_names is None, starts all auto-start servers.
        """
        if server_names is None:
            servers = self.registry.list_auto_start()
        else:
            servers = [self.registry.get(name) for name in server_names]
            servers = [s for s in servers if s is not None]
        
        for config in servers:
            await self.connect(config.name)
        
        # Discover tools from all connected servers
        await self.discover_tools()
    
    async def stop(self):
        """Stop all MCP server connections"""
        async with self._lock:
            for conn in list(self._connections.values()):
                await conn.disconnect()
            self._connections.clear()
            self._tools_cache.clear()
        
        logger.info("mcp_manager_stopped")
    
    async def connect(self, server_name: str) -> bool:
        """Connect to a specific MCP server"""
        async with self._lock:
            if server_name in self._connections:
                return self._connections[server_name].is_connected
            
            config = self.registry.get(server_name)
            if not config:
                logger.error(f"Server not found: {server_name}")
                return False
            
            if not config.enabled:
                logger.warning(f"Server disabled: {server_name}")
                return False
            
            conn = MCPServerConnection(config)
            success = await conn.connect()
            
            if success:
                self._connections[server_name] = conn
            
            return success
    
    async def disconnect(self, server_name: str):
        """Disconnect from a specific MCP server"""
        async with self._lock:
            if server_name in self._connections:
                await self._connections[server_name].disconnect()
                del self._connections[server_name]
                
                # Remove tools from this server
                self._tools_cache = {
                    k: v for k, v in self._tools_cache.items()
                    if v.server_name != server_name
                }
    
    async def discover_tools(self) -> List[MCPTool]:
        """Discover all tools from connected servers"""
        all_tools = []
        
        for conn in self._connections.values():
            if conn.is_connected:
                tools = conn.get_tools()
                all_tools.extend(tools)
                
                # Cache tools
                for tool in tools:
                    self._tools_cache[tool.name] = tool
        
        logger.info(f"mcp_tools_discovered", count=len(all_tools))
        return all_tools
    
    def get_tools(self) -> List[MCPTool]:
        """Get all available tools"""
        return list(self._tools_cache.values())
    
    def get_tool(self, name: str) -> Optional[MCPTool]:
        """Get a specific tool by name"""
        return self._tools_cache.get(name)
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPToolResult:
        """
        Execute a tool by name.
        
        Routes the call to the appropriate MCP server.
        """
        tool = self._tools_cache.get(tool_name)
        if not tool:
            return MCPToolResult.from_error(f"Tool not found: {tool_name}")
        
        conn = self._connections.get(tool.server_name)
        if not conn or not conn.is_connected:
            return MCPToolResult.from_error(f"Server not connected: {tool.server_name}")
        
        return await conn.call_tool(tool_name, arguments)
    
    def get_tools_for_claude(self) -> List[Dict[str, Any]]:
        """
        Get tools in Claude API format.
        
        Converts MCP tools to the format expected by Claude's tool_use.
        """
        claude_tools = []
        
        for tool in self._tools_cache.values():
            claude_tools.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            })
        
        return claude_tools
    
    @property
    def connected_servers(self) -> List[str]:
        """Get list of connected server names"""
        return [
            name for name, conn in self._connections.items()
            if conn.is_connected
        ]


# Global manager instance
_manager: Optional[MCPManager] = None


def get_manager() -> MCPManager:
    """Get the global MCP manager"""
    global _manager
    if _manager is None:
        _manager = MCPManager()
    return _manager


@asynccontextmanager
async def mcp_session():
    """
    Context manager for MCP session.
    
    Usage:
        async with mcp_session() as manager:
            tools = manager.get_tools()
            result = await manager.call_tool("filesystem_read_file", {"path": "test.txt"})
    """
    manager = get_manager()
    await manager.start()
    try:
        yield manager
    finally:
        await manager.stop()
