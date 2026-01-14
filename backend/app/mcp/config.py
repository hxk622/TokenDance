"""
MCP Configuration Loader

Loads MCP server configurations from mcp.json file with environment variable expansion.
"""
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)


class MCPSettings(BaseModel):
    """Global MCP settings"""
    auto_start_enabled: bool = True
    connection_timeout_ms: int = 30000
    tool_execution_timeout_ms: int = 60000


class MCPPermissions(BaseModel):
    """Permission settings for MCP tools"""
    default_policy: str = "allow"  # "allow" or "deny"
    tool_whitelist: List[str] = Field(default_factory=list)
    tool_blacklist: List[str] = Field(default_factory=list)
    allowed_paths: List[str] = Field(default_factory=list)
    denied_paths: List[str] = Field(default_factory=list)


class MCPServerConfigJSON(BaseModel):
    """Server configuration from JSON"""
    description: str = ""
    transport: str = "stdio"  # "stdio" or "http"
    command: Optional[str] = None  # For stdio
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)
    url: Optional[str] = None  # For http
    headers: Dict[str, str] = Field(default_factory=dict)
    capabilities: List[str] = Field(default_factory=lambda: ["tools"])
    auto_start: bool = False
    enabled: Any = True  # Can be bool or string with env var


class MCPConfig(BaseModel):
    """Complete MCP configuration"""
    version: str = "1.0"
    settings: MCPSettings = Field(default_factory=MCPSettings)
    permissions: MCPPermissions = Field(default_factory=MCPPermissions)
    servers: Dict[str, MCPServerConfigJSON] = Field(default_factory=dict)


def expand_env_vars(value: Any) -> Any:
    """
    Expand environment variables in configuration values.
    
    Supports:
    - ${VAR} - simple expansion
    - ${VAR:-default} - expansion with default
    - ${VAR:?false} - expansion, returns false if not set
    """
    if isinstance(value, str):
        # Pattern: ${VAR}, ${VAR:-default}, ${VAR:?false}
        pattern = r'\$\{([^}:]+)(?::-([^}]*))?(?::\?([^}]*))?\}'
        
        def replacer(match):
            var_name = match.group(1)
            default_value = match.group(2)
            check_value = match.group(3)
            
            env_value = os.environ.get(var_name)
            
            if env_value:
                return env_value
            elif check_value is not None:
                # ${VAR:?false} - return check_value if VAR not set
                return check_value
            elif default_value is not None:
                # ${VAR:-default} - return default if VAR not set
                return default_value
            else:
                # ${VAR} - return empty string if not set
                return ""
        
        result = re.sub(pattern, replacer, value)
        
        # Handle boolean-like strings
        if result.lower() == "true":
            return True
        elif result.lower() == "false":
            return False
        
        return result
    
    elif isinstance(value, dict):
        return {k: expand_env_vars(v) for k, v in value.items()}
    
    elif isinstance(value, list):
        return [expand_env_vars(v) for v in value]
    
    return value


def load_mcp_config(config_path: Optional[str] = None) -> MCPConfig:
    """
    Load MCP configuration from JSON file.
    
    Args:
        config_path: Path to mcp.json. If None, searches in default locations.
    
    Returns:
        MCPConfig object with expanded environment variables.
    """
    # Default search paths
    search_paths = [
        config_path,
        os.environ.get("MCP_CONFIG_PATH"),
        "mcp.json",
        "config/mcp.json",
        "../mcp.json",
        Path(__file__).parent.parent.parent / "mcp.json",  # backend/mcp.json
    ]
    
    config_file = None
    for path in search_paths:
        if path and Path(path).exists():
            config_file = Path(path)
            break
    
    if not config_file:
        logger.warning("mcp.json not found, using default configuration")
        return MCPConfig()
    
    logger.info("mcp_config_loading", path=str(config_file))
    
    try:
        with open(config_file, "r") as f:
            raw_config = json.load(f)
        
        # Expand environment variables
        expanded_config = expand_env_vars(raw_config)
        
        # Parse into model
        config = MCPConfig(**expanded_config)
        
        logger.info(
            "mcp_config_loaded",
            servers=len(config.servers),
            enabled=[name for name, srv in config.servers.items() if srv.enabled],
        )
        
        return config
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in mcp.json: {e}")
        return MCPConfig()
    except Exception as e:
        logger.error(f"Failed to load mcp.json: {e}")
        return MCPConfig()


# Global config instance
_config: Optional[MCPConfig] = None


def get_mcp_config() -> MCPConfig:
    """Get the global MCP configuration"""
    global _config
    if _config is None:
        _config = load_mcp_config()
    return _config


def reload_mcp_config(config_path: Optional[str] = None) -> MCPConfig:
    """Reload MCP configuration"""
    global _config
    _config = load_mcp_config(config_path)
    return _config
