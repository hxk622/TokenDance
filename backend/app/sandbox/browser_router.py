"""
浏览器路由器

解决问题：External Browser vs AIO Sandbox 内置浏览器两个入口

路由策略：
- 需要与 Sandbox 共享文件系统 → AIO Sandbox Browser
- Deep Research → AIO Sandbox Browser（结果持久化）
- 简单操作 → External Browser（更轻量）

修复：单实例模式，同一时间只保持一个浏览器实例，切换时自动关闭。
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class BrowserBackend(str, Enum):
    """浏览器后端"""

    EXTERNAL = "external"  # 外部浏览器 (agent-browser)
    AIO_SANDBOX = "aio_sandbox"  # AIO Sandbox 内置


@dataclass
class BrowserAction:
    """浏览器操作"""

    action: str  # navigate, click, fill, screenshot, close
    params: dict[str, Any]


@dataclass
class BrowserResult:
    """浏览器操作结果"""

    success: bool
    data: Any = None
    error: str | None = None
    screenshot: bytes | None = None


class BrowserRouter:
    """浏览器路由器

    修复问题 #5：单实例模式
    - 同一时间只保持一个浏览器实例
    - 切换后端时自动关闭当前浏览器
    """

    def __init__(
        self,
        session_id: str,
        aio_sandbox: Any | None = None,
    ):
        """
        Args:
            session_id: 会话 ID
            aio_sandbox: AIOSandboxClient 实例（可选）
        """
        self.session_id = session_id
        self._aio_sandbox = aio_sandbox

        # 单实例状态
        self._current_backend: BrowserBackend | None = None
        self._browser: Any | None = None

    def select_backend(self, context: dict[str, Any]) -> BrowserBackend:
        """选择浏览器后端

        Args:
            context: 上下文信息
                - needs_file_access: 是否需要访问文件系统
                - is_research: 是否是研究任务

        Returns:
            BrowserBackend: 选择的后端
        """
        # 需要与 Sandbox 共享文件系统
        if context.get("needs_file_access"):
            return BrowserBackend.AIO_SANDBOX

        # 研究任务需要持久化
        if context.get("is_research"):
            return BrowserBackend.AIO_SANDBOX

        # 默认使用外部浏览器（更轻量）
        return BrowserBackend.EXTERNAL

    async def execute(
        self,
        action: BrowserAction,
        context: dict[str, Any] | None = None,
        backend: BrowserBackend | None = None,
    ) -> BrowserResult:
        """执行浏览器操作

        Args:
            action: 浏览器操作
            context: 上下文信息
            backend: 强制指定后端（可选）

        Returns:
            BrowserResult: 操作结果
        """
        target_backend = backend or self.select_backend(context or {})

        # 检查是否需要切换后端（单实例模式）
        if self._current_backend and self._current_backend != target_backend:
            logger.info(
                f"切换浏览器后端: {self._current_backend.value} -> {target_backend.value}"
            )
            await self._close_current()

        # 确保有浏览器实例
        if not self._browser:
            self._browser = await self._create_browser(target_backend)
            self._current_backend = target_backend

        # 执行操作
        logger.info(f"Browser [{target_backend.value}]: {action.action}")
        return await self._execute_action(action)

    async def _create_browser(self, backend: BrowserBackend) -> Any:
        """创建浏览器实例"""
        if backend == BrowserBackend.AIO_SANDBOX:
            if not self._aio_sandbox:
                return BrowserResult(success=False, error="AIO Sandbox 不可用")
            # AIO Sandbox 浏览器直接使用 sandbox 实例
            return self._aio_sandbox
        else:
            # 外部浏览器
            try:
                from app.agent.tools.builtin.browser_ops import create_browser_session

                return await create_browser_session(self.session_id)
            except ImportError as e:
                logger.warning("browser_ops 模块不可用，回退到 AIO Sandbox")
                if self._aio_sandbox:
                    self._current_backend = BrowserBackend.AIO_SANDBOX
                    return self._aio_sandbox
                raise RuntimeError("没有可用的浏览器后端") from e

    async def _execute_action(self, action: BrowserAction) -> BrowserResult:
        """执行浏览器操作"""
        if not self._browser:
            return BrowserResult(success=False, error="浏览器未初始化")

        try:
            if self._current_backend == BrowserBackend.AIO_SANDBOX:
                return await self._execute_aio(action)
            else:
                return await self._execute_external(action)
        except Exception as e:
            logger.error(f"浏览器操作失败: {e}")
            return BrowserResult(success=False, error=str(e))

    async def _execute_aio(self, action: BrowserAction) -> BrowserResult:
        """AIO Sandbox 浏览器操作"""
        if action.action == "navigate":
            await self._browser.browser_navigate(action.params["url"])
            return BrowserResult(success=True)
        elif action.action == "screenshot":
            img = await self._browser.browser_screenshot(action.params.get("url"))
            return BrowserResult(success=True, screenshot=img)
        elif action.action == "click":
            await self._browser.browser_click(action.params["selector"])
            return BrowserResult(success=True)
        elif action.action == "fill":
            await self._browser.browser_fill(action.params["selector"], action.params["value"])
            return BrowserResult(success=True)
        elif action.action == "get_content":
            content = await self._browser.browser_get_content()
            return BrowserResult(success=True, data=content)
        elif action.action == "close":
            # AIO Sandbox 浏览器通常不单独关闭
            return BrowserResult(success=True)
        else:
            return BrowserResult(success=False, error=f"未知操作: {action.action}")

    async def _execute_external(self, action: BrowserAction) -> BrowserResult:
        """外部浏览器操作"""
        if action.action == "navigate":
            result = await self._browser.navigate(action.params["url"])
            return BrowserResult(success=True, data=result)
        elif action.action == "screenshot":
            img = await self._browser.screenshot()
            return BrowserResult(success=True, screenshot=img)
        elif action.action == "click":
            await self._browser.click(action.params["selector"])
            return BrowserResult(success=True)
        elif action.action == "fill":
            await self._browser.fill(action.params["selector"], action.params["value"])
            return BrowserResult(success=True)
        elif action.action == "get_content":
            content = await self._browser.get_content()
            return BrowserResult(success=True, data=content)
        elif action.action == "close":
            await self._browser.close()
            self._browser = None
            self._current_backend = None
            return BrowserResult(success=True)
        else:
            return BrowserResult(success=False, error=f"未知操作: {action.action}")

    async def _close_current(self) -> None:
        """关闭当前浏览器"""
        if not self._browser:
            return

        try:
            if self._current_backend == BrowserBackend.EXTERNAL:
                await self._browser.close()
        except Exception as e:
            logger.warning(f"关闭浏览器失败: {e}")
        finally:
            self._browser = None
            self._current_backend = None

    async def cleanup(self) -> None:
        """清理资源"""
        await self._close_current()

    @property
    def current_backend(self) -> BrowserBackend | None:
        """当前使用的后端"""
        return self._current_backend

    @property
    def is_active(self) -> bool:
        """是否有活跃的浏览器"""
        return self._browser is not None
