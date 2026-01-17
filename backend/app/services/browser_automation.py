"""
Browser Automation Service
==========================

基于 Vercel Labs agent-browser 的浏览器自动化服务。

核心优势:
- 93% Token 节省 (Snapshot + Refs vs 完整 DOM)
- 确定性元素选择 (@e1, @e2)
- Session 隔离支持

使用示例:
    browser = AgentBrowserService(session="task_123")
    snapshot = await browser.open("https://example.com")
    # snapshot.tree: "- link \"More info\" [ref=e1]"
    await browser.click("@e1")
    await browser.close()
"""

import asyncio
import json
import logging
import os
import shutil
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


# ============================================================================
# Error Types
# ============================================================================

class BrowserErrorType(Enum):
    """浏览器错误类型"""
    TIMEOUT = "timeout"
    ELEMENT_NOT_FOUND = "element_not_found"
    NETWORK_ERROR = "network_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    SESSION_CLOSED = "session_closed"
    UNKNOWN = "unknown"


class BrowserError(Exception):
    """浏览器操作异常"""

    def __init__(
        self,
        message: str,
        error_type: BrowserErrorType = BrowserErrorType.UNKNOWN,
        recoverable: bool = True
    ):
        super().__init__(message)
        self.error_type = error_type
        self.recoverable = recoverable

    @classmethod
    def timeout(cls, operation: str, timeout: float) -> "BrowserError":
        return cls(
            f"{operation} timed out after {timeout}s",
            BrowserErrorType.TIMEOUT,
            recoverable=True
        )

    @classmethod
    def element_not_found(cls, ref: str) -> "BrowserError":
        return cls(
            f"Element not found: {ref}",
            BrowserErrorType.ELEMENT_NOT_FOUND,
            recoverable=True
        )

    @classmethod
    def network_error(cls, url: str, detail: str = "") -> "BrowserError":
        return cls(
            f"Network error accessing {url}: {detail}",
            BrowserErrorType.NETWORK_ERROR,
            recoverable=True
        )

    @classmethod
    def service_unavailable(cls, service: str) -> "BrowserError":
        return cls(
            f"{service} is not available",
            BrowserErrorType.SERVICE_UNAVAILABLE,
            recoverable=False
        )


@dataclass
class SnapshotResult:
    """
    Snapshot 结果

    包含 Accessibility Tree 的文本表示和元素引用映射。
    """
    tree: str                           # Accessibility Tree 文本
    refs: dict[str, str] = field(default_factory=dict)  # ref -> element description
    url: str = ""
    title: str = ""

    @classmethod
    def from_text(cls, text: str, url: str = "", title: str = "") -> "SnapshotResult":
        """从 agent-browser 文本输出解析"""
        refs = {}
        lines = text.strip().split("\n")
        for line in lines:
            # 解析格式: "- link \"More info\" [ref=e1]"
            if "[ref=" in line:
                start = line.find("[ref=") + 5
                end = line.find("]", start)
                if start > 4 and end > start:
                    ref = line[start:end]
                    refs[f"@{ref}"] = line

        return cls(tree=text, refs=refs, url=url, title=title)

    @classmethod
    def from_json(cls, json_str: str) -> "SnapshotResult":
        """从 JSON 输出解析"""
        try:
            data = json.loads(json_str)
            return cls(
                tree=data.get("tree", ""),
                refs=data.get("refs", {}),
                url=data.get("url", ""),
                title=data.get("title", "")
            )
        except json.JSONDecodeError:
            # 降级为文本解析
            return cls.from_text(json_str)


@dataclass
class BrowserResult:
    """浏览器操作结果"""
    success: bool
    data: Any | None = None
    error: str | None = None
    screenshot_path: str | None = None
    duration_ms: float = 0


class BrowserAutomationService(ABC):
    """
    浏览器自动化服务抽象接口

    定义统一的浏览器操作接口，支持多种实现：
    - AgentBrowserService: 基于 agent-browser CLI
    - PlaywrightService: 基于原生 Playwright (降级方案)
    """

    @abstractmethod
    async def open(self, url: str) -> SnapshotResult:
        """打开URL并返回Snapshot"""
        pass

    @abstractmethod
    async def snapshot(
        self,
        interactive_only: bool = True,
        compact: bool = True,
        max_depth: int | None = None
    ) -> SnapshotResult:
        """获取当前页面Snapshot"""
        pass

    @abstractmethod
    async def click(self, ref: str) -> BrowserResult:
        """点击元素"""
        pass

    @abstractmethod
    async def fill(self, ref: str, text: str) -> BrowserResult:
        """填充输入框"""
        pass

    @abstractmethod
    async def get_text(self, ref: str) -> str:
        """获取元素文本"""
        pass

    @abstractmethod
    async def screenshot(self, path: str | None = None) -> str:
        """截图并返回路径"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """关闭浏览器"""
        pass

    @abstractmethod
    async def is_open(self) -> bool:
        """检查浏览器是否打开"""
        pass


class AgentBrowserService(BrowserAutomationService):
    """
    agent-browser CLI 实现

    核心优势:
    - 93% Token 节省 (Snapshot + Refs vs 完整 DOM)
    - 确定性元素选择 (@e1, @e2)
    - Session 隔离支持

    使用示例:
        async with AgentBrowserService(session="task_123") as browser:
            snapshot = await browser.open("https://example.com")
            await browser.click("@e1")
    """

    def __init__(
        self,
        session: str | None = None,
        timeout: float = 30.0,
        headless: bool = True,
        screenshots_dir: str = "/tmp/tokendance/screenshots"
    ):
        """
        初始化浏览器服务

        Args:
            session: Session ID，用于隔离多个浏览器实例
            timeout: 命令执行超时时间（秒）
            headless: 是否无头模式
            screenshots_dir: 截图保存目录
        """
        self.session = session or f"td_{uuid4().hex[:8]}"
        self.timeout = timeout
        self.headless = headless
        self.screenshots_dir = screenshots_dir
        self._is_open = False
        self._current_url = ""
        self._current_title = ""

    def _build_base_cmd(self) -> list[str]:
        """构建基础命令"""
        cmd = ["agent-browser", "--session", self.session]
        if self.headless:
            # agent-browser 默认是 headless，--headed 才是显示窗口
            pass
        else:
            cmd.append("--headed")
        return cmd

    async def _run_cmd(
        self,
        args: list[str],
        json_output: bool = False,
        timeout: float | None = None
    ) -> str:
        """
        执行 agent-browser 命令

        Args:
            args: 命令参数
            json_output: 是否请求 JSON 输出
            timeout: 超时时间（秒），None 使用默认值

        Returns:
            命令输出文本

        Raises:
            RuntimeError: 命令执行失败
            asyncio.TimeoutError: 命令超时
        """
        cmd = self._build_base_cmd() + args
        if json_output:
            cmd.append("--json")

        timeout = timeout or self.timeout

        logger.debug(f"Running command: {' '.join(cmd)}")
        start_time = time.time()

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            duration = (time.time() - start_time) * 1000

            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"Command failed: {error_msg}")
                raise RuntimeError(f"agent-browser error: {error_msg}")

            output = stdout.decode().strip()
            logger.debug(f"Command completed in {duration:.0f}ms: {output[:200]}...")
            return output

        except TimeoutError:
            logger.error(f"Command timed out after {timeout}s")
            raise

    async def open(self, url: str) -> SnapshotResult:
        """
        打开URL并返回Snapshot

        Args:
            url: 要打开的URL

        Returns:
            SnapshotResult 包含页面结构和元素引用
        """
        output = await self._run_cmd(["open", url])
        self._is_open = True

        # 解析输出: "✓ Example Domain\n  https://example.com/"
        lines = output.strip().split("\n")
        if lines:
            title_line = lines[0].replace("✓ ", "").strip()
            self._current_title = title_line
        if len(lines) > 1:
            self._current_url = lines[1].strip()
        else:
            self._current_url = url

        # 获取 snapshot
        return await self.snapshot()

    async def snapshot(
        self,
        interactive_only: bool = True,
        compact: bool = True,
        max_depth: int | None = None
    ) -> SnapshotResult:
        """
        获取 Accessibility Tree Snapshot

        关键参数:
        - interactive_only (-i): 只返回交互元素 (button, input, link)
        - compact (-c): 紧凑模式 (移除空结构元素)

        这两个参数是 93% Token 节省的关键!

        Args:
            interactive_only: 只返回交互元素
            compact: 紧凑模式
            max_depth: 最大深度限制

        Returns:
            SnapshotResult
        """
        args = ["snapshot"]
        if interactive_only:
            args.append("-i")
        if compact:
            args.append("-c")
        if max_depth is not None:
            args.extend(["-d", str(max_depth)])

        output = await self._run_cmd(args)

        return SnapshotResult.from_text(
            output,
            url=self._current_url,
            title=self._current_title
        )

    async def click(self, ref: str) -> BrowserResult:
        """
        点击元素

        Args:
            ref: 元素引用，格式为 @e1, @e2 等

        Returns:
            BrowserResult
        """
        start_time = time.time()
        try:
            await self._run_cmd(["click", ref])
            duration = (time.time() - start_time) * 1000
            return BrowserResult(success=True, duration_ms=duration)
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return BrowserResult(success=False, error=str(e), duration_ms=duration)

    async def fill(self, ref: str, text: str) -> BrowserResult:
        """
        填充输入框

        Args:
            ref: 元素引用
            text: 要填充的文本

        Returns:
            BrowserResult
        """
        start_time = time.time()
        try:
            await self._run_cmd(["fill", ref, text])
            duration = (time.time() - start_time) * 1000
            return BrowserResult(success=True, duration_ms=duration)
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return BrowserResult(success=False, error=str(e), duration_ms=duration)

    async def get_text(self, ref: str) -> str:
        """
        获取元素文本

        Args:
            ref: 元素引用

        Returns:
            元素文本内容
        """
        output = await self._run_cmd(["get", "text", ref])
        return output.strip()

    async def screenshot(self, path: str | None = None) -> str:
        """
        截图

        Args:
            path: 保存路径，None 则自动生成

        Returns:
            截图文件路径
        """
        import os

        if path is None:
            os.makedirs(self.screenshots_dir, exist_ok=True)
            path = os.path.join(
                self.screenshots_dir,
                f"{self.session}_{int(time.time() * 1000)}.png"
            )

        await self._run_cmd(["screenshot", path])
        return path

    async def close(self) -> None:
        """关闭浏览器"""
        if self._is_open:
            try:
                await self._run_cmd(["close"])
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
            finally:
                self._is_open = False

    async def is_open(self) -> bool:
        """检查浏览器是否打开"""
        return self._is_open

    # Context manager 支持
    async def __aenter__(self) -> "AgentBrowserService":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()


# ============================================================================
# Playwright Fallback Service
# ============================================================================

class PlaywrightFallbackService(BrowserAutomationService):
    """
    Playwright 降级方案

    当 agent-browser 不可用时使用。
    Token 效率较低，但更稳定。
    """

    def __init__(
        self,
        session: str | None = None,
        timeout: float = 30.0,
        headless: bool = True,
        screenshots_dir: str = "/tmp/tokendance/screenshots"
    ):
        self.session = session or f"pw_{uuid4().hex[:8]}"
        self.timeout = timeout
        self.headless = headless
        self.screenshots_dir = screenshots_dir
        self._browser = None
        self._page = None
        self._is_open = False
        self._playwright = None

    async def _ensure_browser(self):
        """确保浏览器已启动"""
        if self._browser is None:
            try:
                from playwright.async_api import async_playwright
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(headless=self.headless)
                self._page = await self._browser.new_page()
            except ImportError:
                raise BrowserError.service_unavailable("Playwright")

    async def open(self, url: str) -> SnapshotResult:
        await self._ensure_browser()
        try:
            await self._page.goto(url, timeout=self.timeout * 1000)
            self._is_open = True
            return await self.snapshot()
        except Exception as e:
            raise BrowserError.network_error(url, str(e))

    async def snapshot(
        self,
        interactive_only: bool = True,
        compact: bool = True,
        max_depth: int | None = None
    ) -> SnapshotResult:
        if not self._page:
            raise BrowserError("No page open", BrowserErrorType.SESSION_CLOSED)

        # 使用 Playwright 获取 accessibility tree
        tree = await self._page.accessibility.snapshot()

        # 简化树结构
        def format_node(node: dict, depth: int = 0) -> list[str]:
            if max_depth and depth > max_depth:
                return []

            lines = []
            role = node.get("role", "")
            name = node.get("name", "")

            # 过滤非交互元素
            interactive_roles = {"button", "link", "textbox", "checkbox", "radio", "combobox"}
            if interactive_only and role not in interactive_roles:
                pass
            else:
                indent = "  " * depth
                lines.append(f"{indent}- {role} \"{name}\"")

            for child in node.get("children", []):
                lines.extend(format_node(child, depth + 1))

            return lines

        tree_text = "\n".join(format_node(tree)) if tree else ""

        return SnapshotResult(
            tree=tree_text,
            refs={},
            url=self._page.url,
            title=await self._page.title()
        )

    async def click(self, ref: str) -> BrowserResult:
        """Playwright 使用 CSS 选择器而非 ref"""
        start_time = time.time()
        try:
            # ref 格式: @e1 -> 尝试解析为 xpath 或使用 click by text
            if ref.startswith("@"):
                # Fallback: 无法直接使用 ref，需要 snapshot 获取位置
                return BrowserResult(
                    success=False,
                    error="Playwright fallback does not support @ref, use CSS selector",
                    duration_ms=(time.time() - start_time) * 1000
                )
            await self._page.click(ref, timeout=self.timeout * 1000)
            return BrowserResult(success=True, duration_ms=(time.time() - start_time) * 1000)
        except Exception as e:
            return BrowserResult(
                success=False,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )

    async def fill(self, ref: str, text: str) -> BrowserResult:
        start_time = time.time()
        try:
            if ref.startswith("@"):
                return BrowserResult(
                    success=False,
                    error="Playwright fallback does not support @ref",
                    duration_ms=(time.time() - start_time) * 1000
                )
            await self._page.fill(ref, text, timeout=self.timeout * 1000)
            return BrowserResult(success=True, duration_ms=(time.time() - start_time) * 1000)
        except Exception as e:
            return BrowserResult(
                success=False,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )

    async def get_text(self, ref: str) -> str:
        if ref.startswith("@"):
            return "Error: Playwright fallback does not support @ref"
        return await self._page.text_content(ref) or ""

    async def screenshot(self, path: str | None = None) -> str:
        if path is None:
            os.makedirs(self.screenshots_dir, exist_ok=True)
            path = os.path.join(
                self.screenshots_dir,
                f"{self.session}_{int(time.time() * 1000)}.png"
            )
        await self._page.screenshot(path=path)
        return path

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
            self._browser = None
            self._page = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        self._is_open = False

    async def is_open(self) -> bool:
        return self._is_open

    async def __aenter__(self) -> "PlaywrightFallbackService":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()


# ============================================================================
# Session Manager
# ============================================================================

@dataclass
class BrowserSession:
    """浏览器会话信息"""
    session_id: str
    task_id: str
    service: BrowserAutomationService
    created_at: datetime
    last_activity: datetime
    implementation: str


class BrowserSessionManager:
    """
    浏览器会话管理器

    负责：
    - 多任务 Session 隔离
    - 超时自动清理
    - 并发数量限制
    - 自动降级处理
    """

    def __init__(
        self,
        max_sessions: int = 10,
        session_timeout_minutes: int = 30,
        cleanup_interval_seconds: int = 60,
        prefer_agent_browser: bool = True
    ):
        self.max_sessions = max_sessions
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.cleanup_interval = cleanup_interval_seconds
        self.prefer_agent_browser = prefer_agent_browser

        self._sessions: dict[str, BrowserSession] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: asyncio.Task | None = None
        self._agent_browser_available: bool | None = None

    async def start(self):
        """启动会话管理器"""
        # 检测 agent-browser 可用性
        self._agent_browser_available = await self._check_agent_browser()
        logger.info(f"agent-browser available: {self._agent_browser_available}")

        # 启动清理任务
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """停止会话管理器，关闭所有会话"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # 关闭所有会话
        async with self._lock:
            for session in list(self._sessions.values()):
                await self._close_session(session)
            self._sessions.clear()

    async def _check_agent_browser(self) -> bool:
        """检测 agent-browser 是否可用"""
        if shutil.which("agent-browser") is None:
            return False

        try:
            process = await asyncio.create_subprocess_exec(
                "agent-browser", "--help",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(process.communicate(), timeout=5)
            return process.returncode == 0
        except Exception:
            return False

    async def get_or_create_session(
        self,
        task_id: str,
        force_playwright: bool = False
    ) -> BrowserAutomationService:
        """
        获取或创建浏览器会话

        Args:
            task_id: 任务 ID
            force_playwright: 强制使用 Playwright

        Returns:
            浏览器服务实例
        """
        async with self._lock:
            # 查找现有会话
            if task_id in self._sessions:
                session = self._sessions[task_id]
                session.last_activity = datetime.now()
                return session.service

            # 检查会话数量限制
            if len(self._sessions) >= self.max_sessions:
                # 关闭最旧的会话
                oldest = min(self._sessions.values(), key=lambda s: s.last_activity)
                await self._close_session(oldest)
                del self._sessions[oldest.session_id]

            # 决定使用哪个实现
            use_agent_browser = (
                self.prefer_agent_browser
                and self._agent_browser_available
                and not force_playwright
            )

            # 创建新会话
            session_id = f"{task_id}_{uuid4().hex[:8]}"

            if use_agent_browser:
                service = AgentBrowserService(session=session_id)
                implementation = "agent-browser"
            else:
                service = PlaywrightFallbackService(session=session_id)
                implementation = "playwright"

            session = BrowserSession(
                session_id=session_id,
                task_id=task_id,
                service=service,
                created_at=datetime.now(),
                last_activity=datetime.now(),
                implementation=implementation
            )

            self._sessions[task_id] = session
            logger.info(f"Created browser session: {session_id} ({implementation})")

            return service

    async def close_session(self, task_id: str) -> None:
        """关闭指定任务的会话"""
        async with self._lock:
            if task_id in self._sessions:
                session = self._sessions[task_id]
                await self._close_session(session)
                del self._sessions[task_id]
                logger.info(f"Closed browser session: {session.session_id}")

    async def _close_session(self, session: BrowserSession) -> None:
        """关闭会话（内部方法）"""
        try:
            await session.service.close()
        except Exception as e:
            logger.warning(f"Error closing session {session.session_id}: {e}")

    async def _cleanup_loop(self):
        """定期清理超时会话"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    async def _cleanup_expired_sessions(self):
        """清理超时会话"""
        now = datetime.now()
        expired = []

        async with self._lock:
            for task_id, session in self._sessions.items():
                if now - session.last_activity > self.session_timeout:
                    expired.append(task_id)

            for task_id in expired:
                session = self._sessions[task_id]
                await self._close_session(session)
                del self._sessions[task_id]
                logger.info(f"Cleaned up expired session: {session.session_id}")

    def get_stats(self) -> dict[str, Any]:
        """获取会话统计信息"""
        return {
            "active_sessions": len(self._sessions),
            "max_sessions": self.max_sessions,
            "agent_browser_available": self._agent_browser_available,
            "sessions": [
                {
                    "task_id": s.task_id,
                    "implementation": s.implementation,
                    "created_at": s.created_at.isoformat(),
                    "last_activity": s.last_activity.isoformat(),
                }
                for s in self._sessions.values()
            ]
        }

    @property
    def is_agent_browser_available(self) -> bool:
        return self._agent_browser_available or False


# ============================================================================
# Smart Browser Service with Auto-Fallback
# ============================================================================

class SmartBrowserService(BrowserAutomationService):
    """
    智能浏览器服务

    自动选择最佳实现，支持故障切换。
    优先使用 agent-browser，失败时自动降级到 Playwright。
    """

    def __init__(
        self,
        session: str | None = None,
        timeout: float = 30.0,
        headless: bool = True,
        screenshots_dir: str = "/tmp/tokendance/screenshots",
        max_retries: int = 2
    ):
        self.session = session or f"smart_{uuid4().hex[:8]}"
        self.timeout = timeout
        self.headless = headless
        self.screenshots_dir = screenshots_dir
        self.max_retries = max_retries

        self._primary: AgentBrowserService | None = None
        self._fallback: PlaywrightFallbackService | None = None
        self._active: BrowserAutomationService | None = None
        self._using_fallback = False

    async def _ensure_service(self):
        """确保有可用的服务"""
        if self._active is not None:
            return

        # 尝试 agent-browser
        if shutil.which("agent-browser"):
            self._primary = AgentBrowserService(
                session=self.session,
                timeout=self.timeout,
                headless=self.headless,
                screenshots_dir=self.screenshots_dir
            )
            self._active = self._primary
            self._using_fallback = False
            logger.info("Using agent-browser as primary")
        else:
            # 直接使用 Playwright
            self._fallback = PlaywrightFallbackService(
                session=self.session,
                timeout=self.timeout,
                headless=self.headless,
                screenshots_dir=self.screenshots_dir
            )
            self._active = self._fallback
            self._using_fallback = True
            logger.info("Using Playwright fallback (agent-browser not found)")

    async def _switch_to_fallback(self):
        """切换到 Playwright fallback"""
        if self._using_fallback:
            return

        logger.warning("Switching to Playwright fallback")

        # 关闭主服务
        if self._primary:
            try:
                await self._primary.close()
            except Exception:
                pass

        # 创建 fallback
        self._fallback = PlaywrightFallbackService(
            session=f"{self.session}_fb",
            timeout=self.timeout,
            headless=self.headless,
            screenshots_dir=self.screenshots_dir
        )
        self._active = self._fallback
        self._using_fallback = True

    async def _execute_with_fallback(self, operation: str, func, *args, **kwargs):
        """执行操作，失败时自动切换到 fallback"""
        await self._ensure_service()

        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"{operation} attempt {attempt + 1} failed: {e}")

                if not self._using_fallback and attempt < self.max_retries:
                    await self._switch_to_fallback()
                    # 重置 func 到新服务
                    func = getattr(self._active, operation)
                else:
                    raise

    async def open(self, url: str) -> SnapshotResult:
        await self._ensure_service()
        return await self._execute_with_fallback(
            "open",
            self._active.open,
            url
        )

    async def snapshot(
        self,
        interactive_only: bool = True,
        compact: bool = True,
        max_depth: int | None = None
    ) -> SnapshotResult:
        await self._ensure_service()
        return await self._active.snapshot(interactive_only, compact, max_depth)

    async def click(self, ref: str) -> BrowserResult:
        await self._ensure_service()
        return await self._active.click(ref)

    async def fill(self, ref: str, text: str) -> BrowserResult:
        await self._ensure_service()
        return await self._active.fill(ref, text)

    async def get_text(self, ref: str) -> str:
        await self._ensure_service()
        return await self._active.get_text(ref)

    async def screenshot(self, path: str | None = None) -> str:
        await self._ensure_service()
        return await self._active.screenshot(path)

    async def close(self) -> None:
        if self._primary:
            try:
                await self._primary.close()
            except Exception:
                pass
        if self._fallback:
            try:
                await self._fallback.close()
            except Exception:
                pass
        self._active = None

    async def is_open(self) -> bool:
        if self._active:
            return await self._active.is_open()
        return False

    @property
    def implementation(self) -> str:
        return "playwright" if self._using_fallback else "agent-browser"

    async def __aenter__(self) -> "SmartBrowserService":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()


# ============================================================================
# Factory & Global Instance
# ============================================================================

# 全局会话管理器
_session_manager: BrowserSessionManager | None = None


def get_session_manager() -> BrowserSessionManager:
    """获取全局会话管理器"""
    global _session_manager
    if _session_manager is None:
        _session_manager = BrowserSessionManager()
    return _session_manager


async def init_session_manager():
    """初始化全局会话管理器"""
    manager = get_session_manager()
    await manager.start()
    return manager


async def shutdown_session_manager():
    """关闭全局会话管理器"""
    global _session_manager
    if _session_manager:
        await _session_manager.stop()
        _session_manager = None


def create_browser_service(
    implementation: str = "smart",
    **kwargs
) -> BrowserAutomationService:
    """
    创建浏览器服务实例

    Args:
        implementation: 实现类型
            - "smart": 智能选择（推荐）
            - "agent-browser": 强制使用 agent-browser
            - "playwright": 强制使用 Playwright
        **kwargs: 传递给具体实现的参数

    Returns:
        BrowserAutomationService 实例
    """
    if implementation == "smart":
        return SmartBrowserService(**kwargs)
    elif implementation == "agent-browser":
        return AgentBrowserService(**kwargs)
    elif implementation == "playwright":
        return PlaywrightFallbackService(**kwargs)
    else:
        raise ValueError(f"Unknown implementation: {implementation}")


async def check_browser_health() -> dict[str, Any]:
    """
    健康检查

    Returns:
        健康状态信息
    """
    result = {
        "status": "healthy",
        "agent_browser_available": False,
        "playwright_available": False,
        "active_sessions": 0,
    }

    # 检查 agent-browser
    if shutil.which("agent-browser"):
        try:
            process = await asyncio.create_subprocess_exec(
                "agent-browser", "--help",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(process.communicate(), timeout=5)
            result["agent_browser_available"] = process.returncode == 0
        except Exception:
            pass

    # 检查 Playwright
    try:
        from playwright.async_api import async_playwright  # noqa: F401
        result["playwright_available"] = True
    except ImportError:
        pass

    # 获取会话信息
    manager = get_session_manager()
    result["active_sessions"] = len(manager._sessions)

    # 确定状态
    if not result["agent_browser_available"] and not result["playwright_available"]:
        result["status"] = "unhealthy"
    elif not result["agent_browser_available"]:
        result["status"] = "degraded"

    return result
