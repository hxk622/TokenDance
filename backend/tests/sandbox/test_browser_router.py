"""
BrowserRouter 单元测试
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.sandbox.browser_router import BrowserRouter
from app.sandbox.exceptions import SandboxError


class TestBrowserRouter:
    """BrowserRouter 测试"""

    @pytest.fixture
    def router(self) -> BrowserRouter:
        """创建路由器"""
        return BrowserRouter()

    # ==================== 单例测试 ====================

    def test_singleton_instance(self):
        """确保单例"""
        router1 = BrowserRouter()
        router2 = BrowserRouter()

        assert router1 is router2

    # ==================== 后端切换测试 ====================

    @pytest.mark.asyncio
    async def test_switch_to_docker(self, router: BrowserRouter):
        """切换到 Docker 后端"""
        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client

            await router.switch_backend("docker", docker_client=mock_client)

            assert router.current_backend == "docker"
            assert router._docker_client == mock_client
            assert router._browser is None

    @pytest.mark.asyncio
    async def test_switch_to_aio_sandbox(self, router: BrowserRouter):
        """切换到 AIO Sandbox 后端"""
        await router.switch_backend("aio_sandbox", api_url="http://localhost:8000")

        assert router.current_backend == "aio_sandbox"
        assert router._aio_api_url == "http://localhost:8000"

    @pytest.mark.asyncio
    async def test_switch_to_none(self, router: BrowserRouter):
        """切换到 None（关闭浏览器）"""
        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client

            # 先切换到 Docker
            await router.switch_backend("docker", docker_client=mock_client)

            # 再切换到 None
            await router.switch_backend(None)

            assert router.current_backend is None
            assert router._docker_client is None

    # ==================== 浏览器获取测试 ====================

    @pytest.mark.asyncio
    async def test_get_browser_creates_new_instance(self, router: BrowserRouter):
        """获取浏览器创建新实例"""
        with patch("docker.from_env") as mock_docker, patch(
            "playwright.async_api.async_playwright"
        ) as mock_playwright:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client

            # 模拟 playwright
            mock_pw = AsyncMock()
            mock_browser = AsyncMock()
            mock_pw.chromium.connect_over_cdp = AsyncMock(return_value=mock_browser)
            mock_playwright.return_value.__aenter__.return_value = mock_pw

            await router.switch_backend("docker", docker_client=mock_client)

            # 启动容器
            with patch.object(router, "_ensure_browser_container") as mock_ensure:
                mock_ensure.return_value = ("container_id", "ws://localhost:9222")

                browser = await router.get_browser()

                assert browser == mock_browser
                assert router._browser == mock_browser

    @pytest.mark.asyncio
    async def test_get_browser_reuses_existing(self, router: BrowserRouter):
        """获取浏览器复用现有实例"""
        mock_browser = AsyncMock()
        router._browser = mock_browser
        router.current_backend = "docker"

        browser = await router.get_browser()

        assert browser == mock_browser

    @pytest.mark.asyncio
    async def test_get_browser_no_backend_raises(self, router: BrowserRouter):
        """没有后端时抛出异常"""
        with pytest.raises(SandboxError, match="未设置浏览器后端"):
            await router.get_browser()

    # ==================== 清理测试 ====================

    @pytest.mark.asyncio
    async def test_cleanup_closes_browser(self, router: BrowserRouter):
        """清理关闭浏览器"""
        mock_browser = AsyncMock()
        router._browser = mock_browser
        router.current_backend = "docker"

        await router.cleanup()

        mock_browser.close.assert_called_once()
        assert router._browser is None

    @pytest.mark.asyncio
    async def test_cleanup_stops_container(self, router: BrowserRouter):
        """清理停止容器"""
        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_container = MagicMock()
            mock_client.containers.get.return_value = mock_container
            mock_docker.return_value = mock_client

            router._docker_client = mock_client
            router._browser_container_id = "container_123"
            router.current_backend = "docker"

            await router.cleanup()

            mock_container.stop.assert_called_once()
            mock_container.remove.assert_called_once()

    # ==================== 后端检查测试 ====================

    def test_is_backend_active(self, router: BrowserRouter):
        """检查后端是否激活"""
        router.current_backend = None
        assert not router.is_backend_active()

        router.current_backend = "docker"
        assert router.is_backend_active()

    # ==================== 状态管理测试 ====================

    @pytest.mark.asyncio
    async def test_switch_backend_cleans_up_previous(self, router: BrowserRouter):
        """切换后端时清理旧的"""
        mock_browser = AsyncMock()
        router._browser = mock_browser
        router.current_backend = "docker"

        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_docker.return_value = mock_client

            await router.switch_backend("aio_sandbox", api_url="http://localhost:8000")

            # 旧的浏览器被关闭
            mock_browser.close.assert_called_once()
            assert router.current_backend == "aio_sandbox"
