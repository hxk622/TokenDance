"""
Browser Operations Tools - 浏览器操作工具集

基于 Vercel Labs agent-browser 的浏览器自动化工具。

核心优势:
- 93% Token 节省 (Snapshot + Refs vs 完整 DOM)
- 确定性元素选择 (@e1, @e2)
- Session 隔离支持

工具列表:
- browser_open: 打开网页并获取 Snapshot
- browser_click: 点击页面元素
- browser_fill: 填充输入框
- browser_snapshot: 获取当前页面 Snapshot
- browser_screenshot: 页面截图
- browser_close: 关闭浏览器
"""
import logging
from typing import Any

from ....services.browser_automation import (
    AgentBrowserService,
)
from ..base import BaseTool
from ..risk import OperationCategory, RiskLevel

logger = logging.getLogger(__name__)

# 全局 Session 管理（同一任务内共享浏览器实例）
_browser_sessions: dict[str, AgentBrowserService] = {}


def get_browser_service(session_id: str | None = None) -> AgentBrowserService:
    """获取或创建浏览器服务实例

    Args:
        session_id: Session ID，None 则使用默认 Session

    Returns:
        AgentBrowserService 实例
    """
    session_id = session_id or "default"

    if session_id not in _browser_sessions:
        _browser_sessions[session_id] = AgentBrowserService(session=session_id)

    return _browser_sessions[session_id]


async def cleanup_browser_session(session_id: str | None = None) -> None:
    """清理浏览器 Session

    Args:
        session_id: Session ID，None 则清理所有
    """
    if session_id is None:
        # 清理所有
        for sid, browser in list(_browser_sessions.items()):
            try:
                await browser.close()
            except Exception as e:
                logger.warning(f"Error closing browser session {sid}: {e}")
        _browser_sessions.clear()
    elif session_id in _browser_sessions:
        try:
            await _browser_sessions[session_id].close()
        except Exception as e:
            logger.warning(f"Error closing browser session {session_id}: {e}")
        del _browser_sessions[session_id]


class BrowserOpenTool(BaseTool):
    """打开网页并获取 Snapshot

    使用 agent-browser 打开指定 URL，返回页面的 Accessibility Tree Snapshot。
    Snapshot 使用 @eN 格式的引用标识符，用于后续操作。

    风险等级：NONE（纯读取操作）
    """

    name = "browser_open"
    description = (
        "Open a web page and return an Accessibility Tree Snapshot. "
        "The snapshot shows interactive elements with refs like @e1, @e2. "
        "Use these refs with browser_click, browser_fill to interact with elements. "
        "This is more efficient than read_url when you need to interact with the page."
    )
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL of the web page to open"
            },
            "session_id": {
                "type": "string",
                "description": "Optional session ID for browser isolation. Use the same session_id to continue on the same browser instance."
            }
        },
        "required": ["url"]
    }

    risk_level = RiskLevel.NONE
    operation_categories = [OperationCategory.WEB_READ]
    requires_confirmation = False

    async def execute(self, **kwargs: Any) -> str:
        """执行打开网页

        Args:
            url: 要打开的 URL
            session_id: 可选的 Session ID

        Returns:
            str: Snapshot 结果文本
        """
        url = kwargs.get("url", "")
        session_id = kwargs.get("session_id")

        if not url:
            return "Error: URL parameter is required"

        # 验证 URL 格式
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        logger.info(f"Opening URL: {url}")

        try:
            browser = get_browser_service(session_id)
            snapshot = await browser.open(url)

            # 格式化输出
            result = f"✓ Opened: {snapshot.title}\n"
            result += f"  URL: {snapshot.url}\n\n"
            result += "Interactive elements (use @eN refs for interactions):\n"
            result += snapshot.tree[:5000]  # 限制大小

            if len(snapshot.tree) > 5000:
                result += "\n\n... (snapshot truncated, use browser_snapshot for full view)"

            return result

        except Exception as e:
            logger.error(f"Failed to open URL {url}: {e}", exc_info=True)
            return f"Error opening URL: {str(e)}"


class BrowserClickTool(BaseTool):
    """点击页面元素

    使用 @eN 格式的引用点击 Snapshot 中的元素。
    点击后自动返回新的 Snapshot。

    风险等级：LOW（可能触发页面跳转）
    """

    name = "browser_click"
    description = (
        "Click an element on the current page using its ref from the snapshot. "
        "Refs are in @eN format (e.g., @e1, @e2). "
        "After clicking, returns a new snapshot showing the updated page state."
    )
    parameters = {
        "type": "object",
        "properties": {
            "ref": {
                "type": "string",
                "description": "The element ref to click (e.g., @e1, @e2). Get refs from browser_open or browser_snapshot."
            },
            "session_id": {
                "type": "string",
                "description": "Optional session ID (must match the session used in browser_open)"
            }
        },
        "required": ["ref"]
    }

    risk_level = RiskLevel.LOW
    operation_categories = [OperationCategory.WEB_INTERACT]
    requires_confirmation = False

    async def execute(self, **kwargs: Any) -> str:
        """执行点击操作

        Args:
            ref: 元素引用 (@eN 格式)
            session_id: 可选的 Session ID

        Returns:
            str: 操作结果和新的 Snapshot
        """
        ref = kwargs.get("ref", "")
        session_id = kwargs.get("session_id")

        if not ref:
            return "Error: ref parameter is required (e.g., @e1)"

        # 确保 ref 格式正确
        if not ref.startswith("@"):
            ref = "@" + ref

        logger.info(f"Clicking element: {ref}")

        try:
            browser = get_browser_service(session_id)
            result = await browser.click(ref)

            if not result.success:
                return f"Error clicking {ref}: {result.error}"

            # 获取新的 snapshot
            snapshot = await browser.snapshot()

            output = f"✓ Clicked {ref} ({result.duration_ms:.0f}ms)\n\n"
            output += "New page state:\n"
            output += snapshot.tree[:5000]

            return output

        except Exception as e:
            logger.error(f"Failed to click {ref}: {e}", exc_info=True)
            return f"Error clicking {ref}: {str(e)}"


class BrowserFillTool(BaseTool):
    """填充输入框

    使用 @eN 格式的引用填充输入框。

    风险等级：LOW（填充表单）
    """

    name = "browser_fill"
    description = (
        "Fill an input field with text using its ref from the snapshot. "
        "Refs are in @eN format (e.g., @e1, @e2). "
        "Use this for text inputs, search boxes, form fields, etc."
    )
    parameters = {
        "type": "object",
        "properties": {
            "ref": {
                "type": "string",
                "description": "The input field ref to fill (e.g., @e3)"
            },
            "text": {
                "type": "string",
                "description": "The text to fill into the input field"
            },
            "session_id": {
                "type": "string",
                "description": "Optional session ID"
            }
        },
        "required": ["ref", "text"]
    }

    risk_level = RiskLevel.LOW
    operation_categories = [OperationCategory.WEB_INTERACT]
    requires_confirmation = False

    async def execute(self, **kwargs: Any) -> str:
        """执行填充操作

        Args:
            ref: 输入框引用 (@eN 格式)
            text: 要填充的文本
            session_id: 可选的 Session ID

        Returns:
            str: 操作结果
        """
        ref = kwargs.get("ref", "")
        text = kwargs.get("text", "")
        session_id = kwargs.get("session_id")

        if not ref:
            return "Error: ref parameter is required"
        if not text:
            return "Error: text parameter is required"

        if not ref.startswith("@"):
            ref = "@" + ref

        logger.info(f"Filling {ref} with text: {text[:50]}...")

        try:
            browser = get_browser_service(session_id)
            result = await browser.fill(ref, text)

            if not result.success:
                return f"Error filling {ref}: {result.error}"

            return f"✓ Filled {ref} with: {text[:100]}{'...' if len(text) > 100 else ''}"

        except Exception as e:
            logger.error(f"Failed to fill {ref}: {e}", exc_info=True)
            return f"Error filling {ref}: {str(e)}"


class BrowserSnapshotTool(BaseTool):
    """获取当前页面 Snapshot

    返回当前页面的 Accessibility Tree Snapshot。
    用于在操作后查看页面状态。

    风险等级：NONE（纯读取）
    """

    name = "browser_snapshot"
    description = (
        "Get the current page's Accessibility Tree Snapshot. "
        "Shows all interactive elements with their refs. "
        "Use this to see the current page state after interactions."
    )
    parameters = {
        "type": "object",
        "properties": {
            "interactive_only": {
                "type": "boolean",
                "description": "Only show interactive elements (buttons, links, inputs). Default: true",
                "default": True
            },
            "session_id": {
                "type": "string",
                "description": "Optional session ID"
            }
        },
        "required": []
    }

    risk_level = RiskLevel.NONE
    operation_categories = [OperationCategory.WEB_READ]
    requires_confirmation = False

    async def execute(self, **kwargs: Any) -> str:
        """获取 Snapshot

        Args:
            interactive_only: 是否只显示交互元素
            session_id: 可选的 Session ID

        Returns:
            str: Snapshot 文本
        """
        interactive_only = kwargs.get("interactive_only", True)
        session_id = kwargs.get("session_id")

        try:
            browser = get_browser_service(session_id)
            snapshot = await browser.snapshot(interactive_only=interactive_only, compact=True)

            result = f"Page: {snapshot.title}\n"
            result += f"URL: {snapshot.url}\n\n"
            result += "Interactive elements:\n"
            result += snapshot.tree[:5000]

            return result

        except Exception as e:
            logger.error(f"Failed to get snapshot: {e}", exc_info=True)
            return f"Error getting snapshot: {str(e)}"


class BrowserScreenshotTool(BaseTool):
    """页面截图

    对当前页面进行截图，用于视觉记录。
    截图保存到本地文件系统。

    风险等级：NONE（纯读取）
    """

    name = "browser_screenshot"
    description = (
        "Take a screenshot of the current page. "
        "Use this for visual documentation of important pages or decisions. "
        "Returns the path to the saved screenshot."
    )
    parameters = {
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "Optional session ID"
            }
        },
        "required": []
    }

    risk_level = RiskLevel.NONE
    operation_categories = [OperationCategory.WEB_READ]
    requires_confirmation = False

    async def execute(self, **kwargs: Any) -> str:
        """执行截图

        Args:
            session_id: 可选的 Session ID

        Returns:
            str: 截图文件路径
        """
        session_id = kwargs.get("session_id")

        try:
            browser = get_browser_service(session_id)
            path = await browser.screenshot()

            return f"✓ Screenshot saved: {path}"

        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}", exc_info=True)
            return f"Error taking screenshot: {str(e)}"


class BrowserCloseTool(BaseTool):
    """关闭浏览器

    关闭当前浏览器实例，释放资源。

    风险等级：NONE
    """

    name = "browser_close"
    description = (
        "Close the browser instance and release resources. "
        "Use this when you're done with browser operations."
    )
    parameters = {
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "Optional session ID to close. If not provided, closes the default session."
            }
        },
        "required": []
    }

    risk_level = RiskLevel.NONE
    operation_categories = []
    requires_confirmation = False

    async def execute(self, **kwargs: Any) -> str:
        """关闭浏览器

        Args:
            session_id: 可选的 Session ID

        Returns:
            str: 操作结果
        """
        session_id = kwargs.get("session_id")

        try:
            await cleanup_browser_session(session_id)
            return "✓ Browser session closed"

        except Exception as e:
            logger.error(f"Failed to close browser: {e}", exc_info=True)
            return f"Error closing browser: {str(e)}"


# 便捷函数
def create_browser_tools() -> list:
    """创建所有浏览器工具实例

    Returns:
        list: 工具实例列表
    """
    return [
        BrowserOpenTool(),
        BrowserClickTool(),
        BrowserFillTool(),
        BrowserSnapshotTool(),
        BrowserScreenshotTool(),
        BrowserCloseTool(),
    ]
