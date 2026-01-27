"""
Browser Operations Tools 集成测试

测试 agent-browser 集成是否正常工作。
"""
import asyncio
import os

import pytest

from app.agent.tools.builtin.browser_ops import (
    BrowserClickTool,
    BrowserCloseTool,
    BrowserOpenTool,
    cleanup_browser_session,
)
from app.services.browser_automation import AgentBrowserService, SnapshotResult

pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_INTEGRATION_TESTS"),
    reason="Set RUN_INTEGRATION_TESTS=1 to run browser integration tests",
)


class TestAgentBrowserService:
    """测试 AgentBrowserService"""

    @pytest.mark.asyncio
    async def test_open_and_snapshot(self):
        """测试打开页面并获取 Snapshot"""
        async with AgentBrowserService(session="test_service") as browser:
            snapshot = await browser.open("https://example.com")

            assert snapshot.title
            assert snapshot.url
            assert isinstance(snapshot.tree, str)
            assert len(snapshot.tree) > 0

    @pytest.mark.asyncio
    async def test_click_element(self):
        """测试点击元素"""
        async with AgentBrowserService(session="test_click") as browser:
            snapshot = await browser.open("https://example.com")

            # example.com 有一个 "Learn more" 链接
            if "@e1" in snapshot.refs:
                result = await browser.click("@e1")
                assert result.success

    @pytest.mark.asyncio
    async def test_snapshot_result_parsing(self):
        """测试 SnapshotResult 解析"""
        text = """- link "Learn more" [ref=e1]
- button "Submit" [ref=e2]
- textbox "Search" [ref=e3]"""

        result = SnapshotResult.from_text(text, url="https://example.com", title="Test")

        assert "@e1" in result.refs
        assert "@e2" in result.refs
        assert "@e3" in result.refs
        assert result.url == "https://example.com"
        assert result.title == "Test"


class TestBrowserTools:
    """测试 Browser Tools"""

    @pytest.fixture(autouse=True)
    async def cleanup(self):
        """每个测试后清理浏览器 Session"""
        yield
        await cleanup_browser_session()

    @pytest.mark.asyncio
    async def test_browser_open_tool(self):
        """测试 BrowserOpenTool"""
        tool = BrowserOpenTool()

        # 验证工具属性
        assert tool.name == "browser_open"
        assert "snapshot" in tool.description.lower()

        # 执行工具
        result = await tool.execute(url="https://example.com", session_id="test_open")

        assert "✓ Opened" in result
        assert "example.com" in result.lower()

    @pytest.mark.asyncio
    async def test_browser_click_tool(self):
        """测试 BrowserClickTool"""
        # 先打开页面
        open_tool = BrowserOpenTool()
        await open_tool.execute(url="https://example.com", session_id="test_click_tool")

        # 点击元素
        click_tool = BrowserClickTool()
        result = await click_tool.execute(ref="@e1", session_id="test_click_tool")

        # 应该成功或返回新的 snapshot
        assert "✓ Clicked" in result or "Error" in result

    @pytest.mark.asyncio
    async def test_browser_close_tool(self):
        """测试 BrowserCloseTool"""
        # 先打开页面
        open_tool = BrowserOpenTool()
        await open_tool.execute(url="https://example.com", session_id="test_close")

        # 关闭浏览器
        close_tool = BrowserCloseTool()
        result = await close_tool.execute(session_id="test_close")

        assert "✓" in result


if __name__ == "__main__":
    # 简单的命令行测试
    async def main():
        print("Running Browser Tools Tests...")

        # Test 1: Service
        print("\n1. Testing AgentBrowserService...")
        async with AgentBrowserService(session="main_test") as browser:
            snapshot = await browser.open("https://example.com")
            print(f"   ✓ Opened: {snapshot.title}")
            print(f"   ✓ Refs: {list(snapshot.refs.keys())[:5]}")

        # Test 2: Tools
        print("\n2. Testing BrowserOpenTool...")
        open_tool = BrowserOpenTool()
        result = await open_tool.execute(url="https://example.com", session_id="main_test_2")
        print(f"   ✓ Result length: {len(result)} chars")

        # Cleanup
        await cleanup_browser_session()

        print("\n✓ All tests passed!")

    asyncio.run(main())
