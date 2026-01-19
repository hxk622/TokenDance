"""
AIO Sandbox 客户端

连接到 AIO Sandbox 服务（agent-sandbox）执行代码。
提供完整的执行环境，支持浏览器操作。
"""

import logging
import time
from typing import Any

import httpx

from app.sandbox.exceptions import SandboxNotAvailableError, SandboxTimeoutError
from app.sandbox.executors.base import BaseSandboxExecutor
from app.sandbox.types import ExecutionRequest, ExecutionResult, SandboxType
from app.sandbox.workspace import AgentWorkspace

logger = logging.getLogger(__name__)


class AIOSandboxClient(BaseSandboxExecutor):
    """AIO Sandbox 客户端

    通过 HTTP API 与 agent-sandbox 服务通信。

    特点：
    - 完整的执行环境
    - 支持浏览器操作
    - 文件系统持久化
    """

    def __init__(
        self,
        session_id: str,
        workspace: AgentWorkspace,
        base_url: str = "http://localhost:8080",
        timeout: float = 60.0,
    ):
        super().__init__(session_id, workspace)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._sandbox_id: str | None = None

    async def connect(self) -> None:
        """连接到 AIO Sandbox 服务"""
        self._client = httpx.AsyncClient(timeout=self.timeout)

        try:
            # 创建 sandbox 实例
            response = await self._client.post(
                f"{self.base_url}/sandbox",
                json={
                    "session_id": self.session_id,
                    "workspace_path": str(self.workspace.host_path),
                },
            )
            response.raise_for_status()
            data = response.json()
            self._sandbox_id = data.get("sandbox_id") or data.get("id")
            logger.info(f"AIO Sandbox 连接成功: {self._sandbox_id}")
        except httpx.HTTPError as e:
            raise SandboxNotAvailableError(f"AIO Sandbox 连接失败: {e}")

    async def disconnect(self) -> None:
        """断开连接"""
        if self._client and self._sandbox_id:
            try:
                await self._client.delete(f"{self.base_url}/sandbox/{self._sandbox_id}")
            except Exception as e:
                logger.warning(f"AIO Sandbox 断开失败: {e}")

        if self._client:
            await self._client.aclose()
            self._client = None
        self._sandbox_id = None

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """执行代码"""
        if not self._client or not self._sandbox_id:
            return ExecutionResult(
                success=False,
                error="AIO Sandbox 未连接",
                sandbox_type=SandboxType.AIO_SANDBOX,
            )

        start_time = time.time()

        try:
            response = await self._client.post(
                f"{self.base_url}/sandbox/{self._sandbox_id}/execute",
                json={
                    "code": request.code,
                    "language": request.language,
                    "timeout": request.timeout,
                },
                timeout=request.timeout + 10,  # 额外时间用于网络
            )
            response.raise_for_status()
            data = response.json()

            return ExecutionResult(
                success=data.get("success", False),
                stdout=data.get("stdout", ""),
                stderr=data.get("stderr", ""),
                exit_code=data.get("exit_code", 0),
                error=data.get("error"),
                sandbox_type=SandboxType.AIO_SANDBOX,
                execution_time_ms=(time.time() - start_time) * 1000,
                files_created=data.get("files_created", []),
            )

        except httpx.TimeoutException:
            raise SandboxTimeoutError(f"执行超时 ({request.timeout}s)")
        except httpx.HTTPStatusError as e:
            return ExecutionResult(
                success=False,
                error=f"AIO Sandbox 错误: {e.response.status_code}",
                sandbox_type=SandboxType.AIO_SANDBOX,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            logger.error(f"AIO Sandbox 执行失败: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                sandbox_type=SandboxType.AIO_SANDBOX,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    # ==================== 浏览器操作 ====================

    async def browser_navigate(self, url: str) -> dict[str, Any]:
        """浏览器导航"""
        return await self._browser_action("navigate", {"url": url})

    async def browser_screenshot(self, url: str | None = None) -> bytes | None:
        """浏览器截图"""
        params = {"url": url} if url else {}
        result = await self._browser_action("screenshot", params)
        if result.get("success") and result.get("screenshot"):
            import base64

            return base64.b64decode(result["screenshot"])
        return None

    async def browser_click(self, selector: str) -> dict[str, Any]:
        """浏览器点击"""
        return await self._browser_action("click", {"selector": selector})

    async def browser_fill(self, selector: str, value: str) -> dict[str, Any]:
        """浏览器填充"""
        return await self._browser_action("fill", {"selector": selector, "value": value})

    async def browser_get_content(self) -> str:
        """获取页面内容"""
        result = await self._browser_action("get_content", {})
        return result.get("content", "")

    async def _browser_action(self, action: str, params: dict[str, Any]) -> dict[str, Any]:
        """执行浏览器操作"""
        if not self._client or not self._sandbox_id:
            return {"success": False, "error": "AIO Sandbox 未连接"}

        try:
            response = await self._client.post(
                f"{self.base_url}/sandbox/{self._sandbox_id}/browser",
                json={"action": action, "params": params},
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"浏览器操作失败: {e}")
            return {"success": False, "error": str(e)}

    async def cleanup(self) -> None:
        """清理资源"""
        await self.disconnect()
