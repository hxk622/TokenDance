"""
MCP Server Registry

Manages registration and configuration of MCP servers.
"""
import os
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from app.mcp.types import MCPTransport, MCPCapability
from app.core.logging import get_logger

logger = get_logger(__name__)


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server"""
    name: str = Field(..., description="Unique server identifier")
    description: str = Field(..., description="Human-readable description")
    command: str = Field(..., description="Command to start the server")
    args: List[str] = Field(default_factory=list, description="Command arguments")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    transport: MCPTransport = Field(default=MCPTransport.STDIO)
    capabilities: List[MCPCapability] = Field(default_factory=list)
    enabled: bool = Field(default=True, description="Whether server is enabled")
    auto_start: bool = Field(default=True, description="Start with TokenDance")
    timeout_seconds: int = Field(default=30, description="Tool execution timeout")
    max_retries: int = Field(default=3, description="Max connection retries")

    class Config:
        use_enum_values = True


class MCPServerRegistry:
    """
    Registry for MCP servers.
    
    Provides registration, lookup, and configuration management
    for MCP servers used by TokenDance.
    """
    
    def __init__(self):
        self._servers: Dict[str, MCPServerConfig] = {}
        self._load_builtin_servers()
    
    def _load_builtin_servers(self):
        """Load built-in MCP servers"""
        
        # Filesystem server - Coworker capability
        self.register(MCPServerConfig(
            name="filesystem",
            description="Local filesystem operations (Coworker capability)",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
            capabilities=[MCPCapability.TOOLS],
            env={},
        ))
        
        # Web search server - Manus capability
        brave_api_key = os.getenv("BRAVE_API_KEY", "")
        if brave_api_key:
            self.register(MCPServerConfig(
                name="web-search",
                description="Web search capability (Manus capability)",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-brave-search"],
                capabilities=[MCPCapability.TOOLS],
                env={"BRAVE_API_KEY": brave_api_key},
            ))
        else:
            logger.warning("BRAVE_API_KEY not set, web-search server disabled")
        
        # Memory server - for working memory
        self.register(MCPServerConfig(
            name="memory",
            description="Key-value memory storage",
            command="npx", 
            args=["-y", "@modelcontextprotocol/server-memory"],
            capabilities=[MCPCapability.TOOLS, MCPCapability.RESOURCES],
            enabled=True,
        ))
        
        # Chrome DevTools - optional, disabled by default
        self.register(MCPServerConfig(
            name="chrome-devtools",
            description="Chrome browser automation",
            command="npx",
            args=["-y", "@anthropic/mcp-server-chrome-devtools"],
            capabilities=[MCPCapability.TOOLS],
            enabled=False,  # Opt-in
            auto_start=False,
        ))
        
        logger.info(
            "builtin_servers_loaded",
            total=len(self._servers),
            enabled=len(self.list_enabled()),
        )
    
    def register(self, config: MCPServerConfig) -> None:
        """Register an MCP server configuration"""
        if config.name in self._servers:
            logger.warning(f"Overwriting existing server config: {config.name}")
        
        self._servers[config.name] = config
        logger.debug(f"Registered MCP server: {config.name}")
    
    def unregister(self, name: str) -> bool:
        """Unregister an MCP server"""
        if name in self._servers:
            del self._servers[name]
            logger.debug(f"Unregistered MCP server: {name}")
            return True
        return False
    
    def get(self, name: str) -> Optional[MCPServerConfig]:
        """Get server configuration by name"""
        return self._servers.get(name)
    
    def list_all(self) -> List[MCPServerConfig]:
        """List all registered servers"""
        return list(self._servers.values())
    
    def list_enabled(self) -> List[MCPServerConfig]:
        """List enabled servers"""
        return [s for s in self._servers.values() if s.enabled]
    
    def list_auto_start(self) -> List[MCPServerConfig]:
        """List servers that should auto-start"""
        return [s for s in self._servers.values() if s.enabled and s.auto_start]
    
    def enable(self, name: str) -> bool:
        """Enable a server"""
        server = self.get(name)
        if server:
            server.enabled = True
            return True
        return False
    
    def disable(self, name: str) -> bool:
        """Disable a server"""
        server = self.get(name)
        if server:
            server.enabled = False
            return True
        return False


# Global registry instance
_registry: Optional[MCPServerRegistry] = None


def get_registry() -> MCPServerRegistry:
    """Get the global MCP server registry"""
    global _registry
    if _registry is None:
        _registry = MCPServerRegistry()
    return _registry
