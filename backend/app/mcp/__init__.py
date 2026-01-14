"""
MCP (Model Context Protocol) Integration Module

This module provides MCP server management capabilities for TokenDance,
enabling standardized tool definitions and secure execution environments.

Features:
- mcp.json configuration file support
- Stdio and HTTP transports
- Permission control (whitelist/blacklist)
- Builtin tools interface
"""

from app.mcp.registry import MCPServerRegistry, MCPServerConfig, get_registry
from app.mcp.manager import (
    MCPManager,
    MCPServerConnection,
    RealMCPServerConnection,
    get_manager,
    mcp_session,
    USE_REAL_PROTOCOL,
)
from app.mcp.types import MCPTool, MCPToolResult, MCPTransport, MCPCapability
from app.mcp.protocol import (
    MCPClient,
    MCPStdioTransport,
    MCPHttpTransport,
    MCPError,
    MCPPermissionChecker,
    get_permission_checker,
)
from app.mcp.config import (
    MCPConfig,
    MCPSettings,
    MCPPermissions,
    get_mcp_config,
    reload_mcp_config,
)
from app.mcp.builtin_tools import (
    BuiltinTool,
    BuiltinToolRegistry,
    get_builtin_registry,
)

__all__ = [
    # Types
    "MCPTool",
    "MCPToolResult",
    "MCPTransport",
    "MCPCapability",
    # Config
    "MCPConfig",
    "MCPSettings",
    "MCPPermissions",
    "get_mcp_config",
    "reload_mcp_config",
    # Registry
    "MCPServerRegistry",
    "MCPServerConfig",
    "get_registry",
    # Manager
    "MCPManager",
    "MCPServerConnection",
    "RealMCPServerConnection",
    "get_manager",
    "mcp_session",
    "USE_REAL_PROTOCOL",
    # Protocol
    "MCPClient",
    "MCPStdioTransport",
    "MCPHttpTransport",
    "MCPError",
    # Permission
    "MCPPermissionChecker",
    "get_permission_checker",
    # Builtin Tools
    "BuiltinTool",
    "BuiltinToolRegistry",
    "get_builtin_registry",
]
