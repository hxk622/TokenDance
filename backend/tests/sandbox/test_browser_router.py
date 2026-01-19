"""
BrowserRouter 单元测试
测试浏览器后端选择和切换。
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.sandbox.browser_router import BrowserAction, BrowserBackend, BrowserResult, BrowserRouter


class TestBrowserBackend:
    """BrowserBackend 枚举测试"""

    def test_values(self):
        """检查所有值"""
        assert BrowserBackend.EXTERNAL.value == "external"
        assert BrowserBackend.AIO_SANDBOX.value == "aio_sandbox"


class TestBrowserAction:
    """BrowserAction 测试"""

    def test_create_action(self):
        """创建操作"""
        action = BrowserAction(action="navigate", params={"url": "https://example.com"})

        assert action.action == "navigate"
        assert action.params["url"] == "https://example.com"


class TestBrowserResult:
    """BrowserResult 测试"""

    def test_success_result(self):
        """成功结果"""
        result = BrowserResult(success=True, data={"content": "Hello"})

        assert result.success
        assert result.data["content"] == "Hello"
        assert result.error is None

    def test_failure_result(self):
        """失败结果"""
        result = BrowserResult(success=False, error="浏览器无法连接")

        assert not result.success
        assert result.error == "浏览器无法连接"

    def test_screenshot_result(self):
        """截图结果"""
        screenshot_data = b"\x89PNG\r\n\x1a\n"
        result = BrowserResult(success=True, screenshot=screenshot_data)

        assert result.success
        assert result.screenshot == screenshot_data


class TestBrowserRouter:
    """BrowserRouter 测试"""

    @pytest.fixture
    def router(self) -> BrowserRouter:
        """创建路由器"""
        return BrowserRouter(session_id="test_session")

    # ==================== 后端选择测试 ====================

    def test_select_backend_needs_file_access(self, router: BrowserRouter):
        """需要文件访问时选择 AIO Sandbox"""
        context = {"needs_file_access": True}
        backend = router.select_backend(context)

        assert backend == BrowserBackend.AIO_SANDBOX

    def test_select_backend_research_task(self, router: BrowserRouter):
        """研究任务选择 AIO Sandbox"""
        context = {"is_research": True}
        backend = router.select_backend(context)

        assert backend == BrowserBackend.AIO_SANDBOX

    def test_select_backend_default(self, router: BrowserRouter):
        """默认选择 External"""
        context = {}
        backend = router.select_backend(context)

        assert backend == BrowserBackend.EXTERNAL

    # ==================== 执行测试 ====================

    @pytest.mark.asyncio
    async def test_execute_no_browser(self, router: BrowserRouter):
        """没有浏览器实例时尝试创建"""
        action = BrowserAction(action="navigate", params={"url": "https://example.com"})

        with patch.object(router, "_create_browser", new_callable=AsyncMock) as mock_create:
            mock_browser = AsyncMock()
            mock_create.return_value = mock_browser

            with patch.object(router, "_execute_action", new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = BrowserResult(success=True)

                result = await router.execute(action, backend=BrowserBackend.EXTERNAL)

                assert result.success
                mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_aio_navigate(self, router: BrowserRouter):
        """使用 AIO Sandbox 浏览器导航"""
        mock_sandbox = AsyncMock()
        mock_sandbox.browser_navigate = AsyncMock()
        router._browser = mock_sandbox
        router._current_backend = BrowserBackend.AIO_SANDBOX

        action = BrowserAction(action="navigate", params={"url": "https://example.com"})

        result = await router._execute_aio(action)

        assert result.success
        mock_sandbox.browser_navigate.assert_called_once_with("https://example.com")

    @pytest.mark.asyncio
    async def test_execute_aio_unknown_action(self, router: BrowserRouter):
        """未知操作返回失败"""
        mock_sandbox = AsyncMock()
        router._browser = mock_sandbox
        router._current_backend = BrowserBackend.AIO_SANDBOX

        action = BrowserAction(action="unknown_action", params={})

        result = await router._execute_aio(action)

        assert not result.success
        assert "未知操作" in result.error

    # ==================== 后端状态测试 ====================

    def test_initial_state(self, router: BrowserRouter):
        """初始状态"""
        assert router._current_backend is None
        assert router._browser is None

    def test_set_backend_state(self, router: BrowserRouter):
        """设置后端状态"""
        router._current_backend = BrowserBackend.AIO_SANDBOX
        assert router._current_backend == BrowserBackend.AIO_SANDBOX
