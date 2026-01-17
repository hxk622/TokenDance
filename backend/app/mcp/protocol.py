"""
MCP Protocol Implementation

Real stdio-based communication with MCP servers using JSON-RPC 2.0.
"""
import asyncio
import json
import os
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MCPMessage:
    """JSON-RPC 2.0 Message"""
    jsonrpc: str = "2.0"
    id: str | None = None
    method: str | None = None
    params: dict[str, Any] | None = None
    result: Any | None = None
    error: dict[str, Any] | None = None

    def to_json(self) -> str:
        d = {"jsonrpc": self.jsonrpc}
        if self.id is not None:
            d["id"] = self.id
        if self.method is not None:
            d["method"] = self.method
        if self.params is not None:
            d["params"] = self.params
        if self.result is not None:
            d["result"] = self.result
        if self.error is not None:
            d["error"] = self.error
        return json.dumps(d)

    @classmethod
    def from_json(cls, data: str) -> "MCPMessage":
        d = json.loads(data)
        return cls(
            jsonrpc=d.get("jsonrpc", "2.0"),
            id=d.get("id"),
            method=d.get("method"),
            params=d.get("params"),
            result=d.get("result"),
            error=d.get("error"),
        )


class MCPStdioTransport:
    """
    Stdio transport for MCP protocol.

    Manages subprocess communication with MCP servers.
    """

    def __init__(
        self,
        command: str,
        args: list[str] = None,
        env: dict[str, str] = None,
        cwd: str | None = None,
    ):
        self.command = command
        self.args = args or []
        self.env = env or {}
        self.cwd = cwd

        self._process: asyncio.subprocess.Process | None = None
        self._reader_task: asyncio.Task | None = None
        self._pending_requests: dict[str, asyncio.Future] = {}
        self._notification_handlers: dict[str, Callable] = {}
        self._connected = False
        self._lock = asyncio.Lock()

    async def connect(self) -> bool:
        """Start the MCP server subprocess and establish communication"""
        if self._connected:
            return True

        try:
            # Merge environment
            full_env = {**os.environ, **self.env}

            logger.info(
                "mcp_transport_starting",
                command=self.command,
                args=self.args,
            )

            # Start subprocess
            self._process = await asyncio.create_subprocess_exec(
                self.command,
                *self.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=full_env,
                cwd=self.cwd,
            )

            # Start reader task
            self._reader_task = asyncio.create_task(self._read_loop())

            self._connected = True
            logger.info("mcp_transport_connected", pid=self._process.pid)

            return True

        except FileNotFoundError:
            logger.error(f"MCP server command not found: {self.command}")
            return False
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            return False

    async def disconnect(self):
        """Stop the MCP server subprocess"""
        if not self._connected:
            return

        self._connected = False

        # Cancel reader task
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass

        # Terminate process
        if self._process:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except TimeoutError:
                self._process.kill()
                await self._process.wait()

        # Cancel pending requests
        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()
        self._pending_requests.clear()

        logger.info("mcp_transport_disconnected")

    async def _read_loop(self):
        """Read messages from subprocess stdout"""
        try:
            while self._connected and self._process:
                line = await self._process.stdout.readline()
                if not line:
                    break

                try:
                    msg = MCPMessage.from_json(line.decode().strip())
                    await self._handle_message(msg)
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON from MCP server: {e}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in MCP read loop: {e}")

    async def _handle_message(self, msg: MCPMessage):
        """Handle incoming message from server"""
        if msg.id and msg.id in self._pending_requests:
            # Response to a request
            future = self._pending_requests.pop(msg.id)
            if msg.error:
                future.set_exception(MCPError(msg.error))
            else:
                future.set_result(msg.result)
        elif msg.method:
            # Notification from server
            handler = self._notification_handlers.get(msg.method)
            if handler:
                try:
                    await handler(msg.params)
                except Exception as e:
                    logger.error(f"Error handling notification {msg.method}: {e}")

    async def send_request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> Any:
        """Send a request and wait for response"""
        if not self._connected or not self._process:
            raise MCPError({"code": -1, "message": "Not connected"})

        request_id = str(uuid.uuid4())
        msg = MCPMessage(id=request_id, method=method, params=params)

        # Create future for response
        future = asyncio.get_event_loop().create_future()
        self._pending_requests[request_id] = future

        try:
            # Send request
            data = msg.to_json() + "\n"
            self._process.stdin.write(data.encode())
            await self._process.stdin.drain()

            # Wait for response
            result = await asyncio.wait_for(future, timeout=timeout)
            return result

        except TimeoutError:
            self._pending_requests.pop(request_id, None)
            raise MCPError({"code": -32000, "message": f"Request timeout: {method}"})

    async def send_notification(self, method: str, params: dict[str, Any] | None = None):
        """Send a notification (no response expected)"""
        if not self._connected or not self._process:
            return

        msg = MCPMessage(method=method, params=params)
        data = msg.to_json() + "\n"
        self._process.stdin.write(data.encode())
        await self._process.stdin.drain()

    def on_notification(self, method: str, handler: Callable):
        """Register a notification handler"""
        self._notification_handlers[method] = handler

    @property
    def is_connected(self) -> bool:
        return self._connected and self._process is not None


class MCPError(Exception):
    """MCP protocol error"""
    def __init__(self, error: dict[str, Any]):
        self.code = error.get("code", -1)
        self.message = error.get("message", "Unknown error")
        self.data = error.get("data")
        super().__init__(self.message)


class MCPClient:
    """
    High-level MCP client.

    Wraps the transport and provides convenient methods for MCP operations.
    """

    def __init__(self, transport: MCPStdioTransport):
        self.transport = transport
        self._initialized = False
        self._server_info: dict[str, Any] = {}
        self._capabilities: dict[str, Any] = {}

    async def connect(self) -> bool:
        """Connect and initialize the MCP session"""
        if not await self.transport.connect():
            return False

        try:
            # Initialize session
            result = await self.transport.send_request(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "roots": {"listChanged": True},
                    },
                    "clientInfo": {
                        "name": "TokenDance",
                        "version": "1.0.0",
                    },
                },
            )

            self._server_info = result.get("serverInfo", {})
            self._capabilities = result.get("capabilities", {})

            # Send initialized notification
            await self.transport.send_notification("notifications/initialized")

            self._initialized = True
            logger.info(
                "mcp_client_initialized",
                server=self._server_info.get("name"),
                version=self._server_info.get("version"),
            )

            return True

        except Exception as e:
            logger.error(f"Failed to initialize MCP session: {e}")
            await self.transport.disconnect()
            return False

    async def disconnect(self):
        """Disconnect from the MCP server"""
        self._initialized = False
        await self.transport.disconnect()

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools from the server"""
        if not self._initialized:
            return []

        try:
            result = await self.transport.send_request("tools/list")
            return result.get("tools", [])
        except MCPError as e:
            logger.error(f"Failed to list tools: {e}")
            return []

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a tool on the server"""
        if not self._initialized:
            raise MCPError({"code": -1, "message": "Not initialized"})

        result = await self.transport.send_request(
            "tools/call",
            {"name": name, "arguments": arguments},
        )
        return result

    async def list_resources(self) -> list[dict[str, Any]]:
        """List available resources"""
        if not self._initialized:
            return []

        try:
            result = await self.transport.send_request("resources/list")
            return result.get("resources", [])
        except MCPError as e:
            logger.error(f"Failed to list resources: {e}")
            return []

    async def read_resource(self, uri: str) -> dict[str, Any]:
        """Read a resource"""
        if not self._initialized:
            raise MCPError({"code": -1, "message": "Not initialized"})

        result = await self.transport.send_request(
            "resources/read",
            {"uri": uri},
        )
        return result

    @property
    def server_name(self) -> str:
        return self._server_info.get("name", "unknown")

    @property
    def server_version(self) -> str:
        return self._server_info.get("version", "unknown")

    @property
    def capabilities(self) -> dict[str, Any]:
        return self._capabilities

    @property
    def is_connected(self) -> bool:
        return self._initialized and self.transport.is_connected


# =============================================================================
# HTTP Transport
# =============================================================================

class MCPHttpTransport:
    """
    HTTP transport for MCP protocol.

    Communicates with MCP servers over HTTP/REST.
    Supports both request-response and SSE for streaming.
    """

    def __init__(
        self,
        url: str,
        headers: dict[str, str] = None,
        timeout: float = 30.0,
    ):
        self.url = url.rstrip("/")
        self.headers = headers or {}
        self.timeout = timeout
        self._connected = False
        self._session = None

    async def connect(self) -> bool:
        """Initialize HTTP session"""
        try:
            import aiohttp
            self._session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            )
            self._connected = True
            logger.info("mcp_http_transport_connected", url=self.url)
            return True
        except Exception as e:
            logger.error(f"Failed to create HTTP session: {e}")
            return False

    async def disconnect(self):
        """Close HTTP session"""
        if self._session:
            await self._session.close()
            self._session = None
        self._connected = False
        logger.info("mcp_http_transport_disconnected")

    async def send_request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        timeout: float = None,
    ) -> Any:
        """Send a JSON-RPC request over HTTP"""
        if not self._connected or not self._session:
            raise MCPError({"code": -1, "message": "Not connected"})

        request_id = str(uuid.uuid4())
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {},
        }

        try:
            async with self._session.post(
                f"{self.url}/rpc",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout or self.timeout),
            ) as response:
                if response.status != 200:
                    raise MCPError({
                        "code": response.status,
                        "message": f"HTTP error: {response.status}",
                    })

                result = await response.json()

                if "error" in result:
                    raise MCPError(result["error"])

                return result.get("result")

        except TimeoutError:
            raise MCPError({"code": -32000, "message": f"Request timeout: {method}"})
        except Exception as e:
            if isinstance(e, MCPError):
                raise
            raise MCPError({"code": -1, "message": str(e)})

    async def send_notification(self, method: str, params: dict[str, Any] | None = None):
        """Send a notification (fire-and-forget)"""
        if not self._connected or not self._session:
            return

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
        }

        try:
            async with self._session.post(
                f"{self.url}/rpc",
                json=payload,
            ):
                pass  # Ignore response for notifications
        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")

    def on_notification(self, method: str, handler: Callable):
        """Register notification handler (not supported in HTTP mode)"""
        logger.warning("Notification handlers not supported in HTTP transport")

    @property
    def is_connected(self) -> bool:
        return self._connected and self._session is not None


# =============================================================================
# Permission Control
# =============================================================================

class MCPPermissionChecker:
    """
    Permission checker for MCP tool execution.

    Enforces whitelist/blacklist policies and path restrictions.
    """

    def __init__(
        self,
        default_policy: str = "allow",
        whitelist: list[str] = None,
        blacklist: list[str] = None,
        allowed_paths: list[str] = None,
        denied_paths: list[str] = None,
    ):
        self.default_policy = default_policy  # "allow" or "deny"
        self.whitelist = set(whitelist or [])
        self.blacklist = set(blacklist or [])
        self.allowed_paths = allowed_paths or []
        self.denied_paths = denied_paths or []

    def can_execute(self, tool_name: str, arguments: dict[str, Any] = None) -> tuple[bool, str]:
        """
        Check if tool execution is allowed.

        Returns:
            (allowed: bool, reason: str)
        """
        # Check blacklist first (always deny)
        if tool_name in self.blacklist:
            return False, f"Tool '{tool_name}' is blacklisted"

        # Check whitelist (if whitelist exists and tool not in it)
        if self.whitelist and tool_name not in self.whitelist:
            if self.default_policy == "deny":
                return False, f"Tool '{tool_name}' not in whitelist"

        # Check path restrictions for file operations
        if arguments:
            path = arguments.get("path") or arguments.get("file_path")
            if path:
                path_check = self._check_path(path)
                if not path_check[0]:
                    return path_check

        return True, "allowed"

    def _check_path(self, path: str) -> tuple[bool, str]:
        """Check if path is allowed"""
        import os

        # Expand path
        expanded_path = os.path.expanduser(os.path.expandvars(path))
        abs_path = os.path.abspath(expanded_path)

        # Check denied paths
        for denied in self.denied_paths:
            denied_expanded = os.path.expanduser(os.path.expandvars(denied))
            denied_abs = os.path.abspath(denied_expanded)
            if abs_path.startswith(denied_abs):
                return False, f"Path '{path}' is in denied area: {denied}"

        # Check allowed paths (if specified)
        if self.allowed_paths:
            is_allowed = False
            for allowed in self.allowed_paths:
                allowed_expanded = os.path.expanduser(os.path.expandvars(allowed))
                allowed_abs = os.path.abspath(allowed_expanded)
                if abs_path.startswith(allowed_abs):
                    is_allowed = True
                    break

            if not is_allowed:
                return False, f"Path '{path}' not in allowed areas"

        return True, "path allowed"

    @classmethod
    def from_config(cls) -> "MCPPermissionChecker":
        """Create permission checker from mcp.json config"""
        try:
            from app.mcp.config import get_mcp_config
            config = get_mcp_config()
            perms = config.permissions

            return cls(
                default_policy=perms.default_policy,
                whitelist=perms.tool_whitelist,
                blacklist=perms.tool_blacklist,
                allowed_paths=perms.allowed_paths,
                denied_paths=perms.denied_paths,
            )
        except Exception as e:
            logger.warning(f"Failed to load permissions from config: {e}")
            return cls()  # Default permissive checker


# Global permission checker
_permission_checker: MCPPermissionChecker | None = None


def get_permission_checker() -> MCPPermissionChecker:
    """Get the global permission checker"""
    global _permission_checker
    if _permission_checker is None:
        _permission_checker = MCPPermissionChecker.from_config()
    return _permission_checker
