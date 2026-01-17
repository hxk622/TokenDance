"""
Builtin Tools Interface

Provides a base class for implementing custom tools that don't require MCP servers.
These tools run directly in the Python process for better performance.
"""
import time
from abc import ABC, abstractmethod
from datetime import UTC
from typing import Any

from app.core.logging import get_logger
from app.mcp.types import MCPTool, MCPToolResult

logger = get_logger(__name__)


class BuiltinTool(ABC):
    """
    Base class for builtin tools.

    Subclass this to create custom tools that:
    - Run in-process (faster than MCP subprocess)
    - Have direct access to Python APIs
    - Don't require external MCP server installation

    Example:
        class CalculatorTool(BuiltinTool):
            name = "calculator"
            description = "Perform mathematical calculations"

            @property
            def input_schema(self):
                return {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "Math expression"}
                    },
                    "required": ["expression"]
                }

            async def execute(self, arguments):
                expr = arguments.get("expression")
                result = eval(expr)  # Be careful with eval!
                return {"result": result}
    """

    # Override these in subclass
    name: str = "unnamed_tool"
    description: str = "No description"

    @property
    @abstractmethod
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input"""
        pass

    @abstractmethod
    async def execute(self, arguments: dict[str, Any]) -> Any:
        """
        Execute the tool with given arguments.

        Returns:
            Tool output (will be wrapped in MCPToolResult)

        Raises:
            Exception: On execution failure
        """
        pass

    def to_mcp_tool(self) -> MCPTool:
        """Convert to MCPTool format"""
        return MCPTool(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            server_name="builtin",
        )

    def to_claude_format(self) -> dict[str, Any]:
        """Convert to Claude API format"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }

    async def call(self, arguments: dict[str, Any]) -> MCPToolResult:
        """
        Call the tool and return result.

        This method handles timing and error wrapping.
        """
        start_time = time.time()

        try:
            result = await self.execute(arguments)
            duration_ms = (time.time() - start_time) * 1000

            logger.info(
                "builtin_tool_success",
                tool=self.name,
                duration_ms=duration_ms,
            )

            return MCPToolResult.from_success(result, duration_ms=duration_ms)

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            logger.error(
                "builtin_tool_error",
                tool=self.name,
                error=str(e),
                duration_ms=duration_ms,
            )

            return MCPToolResult.from_error(str(e), duration_ms=duration_ms)


# =============================================================================
# Example Builtin Tools
# =============================================================================

class PythonEvalTool(BuiltinTool):
    """
    Evaluate Python expressions (with safety restrictions).
    """
    name = "python_eval"
    description = "Evaluate a Python expression and return the result. Limited to safe operations."

    ALLOWED_BUILTINS = {
        "abs", "all", "any", "bool", "dict", "float", "int", "len",
        "list", "max", "min", "pow", "range", "round", "set", "sorted",
        "str", "sum", "tuple", "zip", "map", "filter", "enumerate",
    }

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Python expression to evaluate"
                }
            },
            "required": ["expression"]
        }

    async def execute(self, arguments: dict[str, Any]) -> Any:
        expression = arguments.get("expression", "")

        # Create restricted globals
        safe_builtins = {name: getattr(__builtins__, name) if hasattr(__builtins__, name) else eval(name)
                        for name in self.ALLOWED_BUILTINS}
        safe_globals = {"__builtins__": safe_builtins}

        try:
            result = eval(expression, safe_globals, {})
            return {"result": result, "type": type(result).__name__}
        except SyntaxError as e:
            raise ValueError(f"Invalid syntax: {e}") from e
        except Exception as e:
            raise ValueError(f"Evaluation error: {e}") from e


class DateTimeTool(BuiltinTool):
    """
    Get current date/time information.
    """
    name = "datetime"
    description = "Get current date, time, or timestamp information"

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "description": "Output format: 'iso', 'timestamp', 'date', 'time'",
                    "enum": ["iso", "timestamp", "date", "time"],
                    "default": "iso"
                },
                "timezone": {
                    "type": "string",
                    "description": "Timezone name (e.g., 'UTC', 'Asia/Shanghai')",
                    "default": "UTC"
                }
            },
            "required": []
        }

    async def execute(self, arguments: dict[str, Any]) -> Any:
        from datetime import datetime

        fmt = arguments.get("format", "iso")
        tz_name = arguments.get("timezone", "UTC")

        # Get current time
        if tz_name == "UTC":
            now = datetime.now(UTC)
        else:
            try:
                import zoneinfo
                tz = zoneinfo.ZoneInfo(tz_name)
                now = datetime.now(tz)
            except Exception:
                now = datetime.now(UTC)

        if fmt == "timestamp":
            return {"timestamp": now.timestamp()}
        elif fmt == "date":
            return {"date": now.strftime("%Y-%m-%d")}
        elif fmt == "time":
            return {"time": now.strftime("%H:%M:%S")}
        else:
            return {"datetime": now.isoformat()}


class JsonTool(BuiltinTool):
    """
    Parse or format JSON data.
    """
    name = "json"
    description = "Parse JSON string to object or format object to JSON string"

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform: 'parse' or 'stringify'",
                    "enum": ["parse", "stringify"]
                },
                "data": {
                    "type": ["string", "object", "array"],
                    "description": "Data to process"
                },
                "indent": {
                    "type": "integer",
                    "description": "Indentation for stringify (default: 2)",
                    "default": 2
                }
            },
            "required": ["action", "data"]
        }

    async def execute(self, arguments: dict[str, Any]) -> Any:
        import json

        action = arguments.get("action")
        data = arguments.get("data")
        indent = arguments.get("indent", 2)

        if action == "parse":
            if not isinstance(data, str):
                raise ValueError("Data must be a string for parse action")
            return {"result": json.loads(data)}
        elif action == "stringify":
            return {"result": json.dumps(data, indent=indent, ensure_ascii=False)}
        else:
            raise ValueError(f"Unknown action: {action}")


# =============================================================================
# Builtin Tool Registry
# =============================================================================

class BuiltinToolRegistry:
    """
    Registry for builtin tools.
    """

    def __init__(self):
        self._tools: dict[str, BuiltinTool] = {}
        self._load_default_tools()

    def _load_default_tools(self):
        """Load default builtin tools"""
        default_tools = [
            PythonEvalTool(),
            DateTimeTool(),
            JsonTool(),
        ]

        for tool in default_tools:
            self.register(tool)

        logger.info("builtin_tools_loaded", count=len(self._tools))

    def register(self, tool: BuiltinTool) -> None:
        """Register a builtin tool"""
        self._tools[tool.name] = tool
        logger.debug(f"Registered builtin tool: {tool.name}")

    def unregister(self, name: str) -> bool:
        """Unregister a builtin tool"""
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def get(self, name: str) -> BuiltinTool | None:
        """Get a tool by name"""
        return self._tools.get(name)

    def list_all(self) -> list[BuiltinTool]:
        """List all registered tools"""
        return list(self._tools.values())

    def get_mcp_tools(self) -> list[MCPTool]:
        """Get all tools in MCPTool format"""
        return [tool.to_mcp_tool() for tool in self._tools.values()]

    def get_claude_tools(self) -> list[dict[str, Any]]:
        """Get all tools in Claude API format"""
        return [tool.to_claude_format() for tool in self._tools.values()]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> MCPToolResult:
        """Call a builtin tool"""
        tool = self.get(name)
        if not tool:
            return MCPToolResult.from_error(f"Builtin tool not found: {name}")

        return await tool.call(arguments)


# Global registry
_builtin_registry: BuiltinToolRegistry | None = None


def get_builtin_registry() -> BuiltinToolRegistry:
    """Get the global builtin tool registry"""
    global _builtin_registry
    if _builtin_registry is None:
        _builtin_registry = BuiltinToolRegistry()
    return _builtin_registry
