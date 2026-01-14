"""
MCP (Model Context Protocol) Integration Module

This module provides MCP server management capabilities for TokenDance,
enabling standardized tool definitions and secure execution environments.
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
from app.mcp.protocol import MCPClient, MCPStdioTransport, MCPError

__all__ = [
    # Types
    "MCPTool",
    "MCPToolResult",
    "MCPTransport",
    "MCPCapability",
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
    "MCPError",
]
