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

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from uuid import uuid4
import asyncio
import json
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class SnapshotResult:
    """
    Snapshot 结果
    
    包含 Accessibility Tree 的文本表示和元素引用映射。
    """
    tree: str                           # Accessibility Tree 文本
    refs: Dict[str, str] = field(default_factory=dict)  # ref -> element description
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
    data: Optional[Any] = None
    error: Optional[str] = None
    screenshot_path: Optional[str] = None
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
        max_depth: Optional[int] = None
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
    async def screenshot(self, path: Optional[str] = None) -> str:
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
        session: Optional[str] = None,
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
    
    def _build_base_cmd(self) -> List[str]:
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
        args: List[str], 
        json_output: bool = False,
        timeout: Optional[float] = None
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
            
        except asyncio.TimeoutError:
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
        max_depth: Optional[int] = None
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
    
    async def screenshot(self, path: Optional[str] = None) -> str:
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


# 工厂函数
def create_browser_service(
    implementation: str = "agent-browser",
    **kwargs
) -> BrowserAutomationService:
    """
    创建浏览器服务实例
    
    Args:
        implementation: 实现类型 ("agent-browser" | "playwright")
        **kwargs: 传递给具体实现的参数
    
    Returns:
        BrowserAutomationService 实例
    """
    if implementation == "agent-browser":
        return AgentBrowserService(**kwargs)
    elif implementation == "playwright":
        # TODO: 实现 PlaywrightService 作为降级方案
        raise NotImplementedError("PlaywrightService not implemented yet")
    else:
        raise ValueError(f"Unknown implementation: {implementation}")
