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

from app.mcp.builtin_tools import (
    BuiltinTool,
    BuiltinToolRegistry,
    get_builtin_registry,
)
from app.mcp.config import (
    MCPConfig,
    MCPPermissions,
    MCPSettings,
    get_mcp_config,
    reload_mcp_config,
)
from app.mcp.manager import (
    USE_REAL_PROTOCOL,
    MCPManager,
    MCPServerConnection,
    RealMCPServerConnection,
    get_manager,
    mcp_session,
)
from app.mcp.protocol import (
    MCPClient,
    MCPError,
    MCPHttpTransport,
    MCPPermissionChecker,
    MCPStdioTransport,
    get_permission_checker,
)
from app.mcp.registry import MCPServerConfig, MCPServerRegistry, get_registry
from app.mcp.types import MCPCapability, MCPTool, MCPToolResult, MCPTransport

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
