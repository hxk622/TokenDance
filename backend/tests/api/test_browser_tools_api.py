"""
Browser & Tools API Tests

测试浏览器自动化和工具相关 API 端点：

Browser API:
- GET /api/v1/browser/health - 浏览器健康检查
- GET /api/v1/browser/sessions - 获取会话统计
- POST /api/v1/browser/sessions/{task_id}/close - 关闭会话
- POST /api/v1/browser/sessions/cleanup - 清理会话

Tools API:
- GET /api/v1/tools - 列出所有工具
- GET /api/v1/tools/{name} - 获取工具详情
- GET /api/v1/tools/categories/list - 列出工具分类
- GET /api/v1/tools/descriptions/list - 列出工具描述
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ==================== Browser Health Tests ====================

class TestBrowserHealth:
    """浏览器健康检查测试"""

    def test_browser_health_success(self, test_client):
        """测试成功获取浏览器健康状态"""
        with patch("app.api.v1.browser.check_browser_health") as mock_check:
            mock_check.return_value = {
                "status": "healthy",
                "agent_browser_available": True,
                "playwright_available": True,
                "active_sessions": 0
            }

            response = test_client.get("/api/v1/browser/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "agent_browser_available" in data

    def test_browser_health_degraded(self, test_client):
        """测试降级模式"""
        with patch("app.api.v1.browser.check_browser_health") as mock_check:
            mock_check.return_value = {
                "status": "degraded",
                "agent_browser_available": False,
                "playwright_available": True,
                "active_sessions": 1
            }

            response = test_client.get("/api/v1/browser/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"


# ==================== Browser Sessions Tests ====================

class TestBrowserSessions:
    """浏览器会话测试"""

    def test_get_session_stats(self, test_client):
        """测试获取会话统计"""
        with patch("app.api.v1.browser.get_session_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_stats.return_value = {
                "active_sessions": 2,
                "max_sessions": 10,
                "agent_browser_available": True,
                "sessions": [
                    {
                        "task_id": "task-1",
                        "implementation": "playwright",
                        "created_at": "2024-01-01T00:00:00",
                        "last_activity": "2024-01-01T00:01:00"
                    }
                ]
            }
            mock_get_manager.return_value = mock_manager

            response = test_client.get("/api/v1/browser/sessions")

            assert response.status_code == 200
            data = response.json()
            assert data["active_sessions"] == 2

    def test_close_session(self, test_client):
        """测试关闭会话"""
        with patch("app.api.v1.browser.get_session_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.close_session = AsyncMock()
            mock_get_manager.return_value = mock_manager

            response = test_client.post("/api/v1/browser/sessions/task-123/close")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "closed"
            assert data["task_id"] == "task-123"

    def test_cleanup_sessions(self, test_client):
        """测试清理会话"""
        with patch("app.api.v1.browser.get_session_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager._cleanup_expired_sessions = AsyncMock()
            mock_get_manager.return_value = mock_manager

            response = test_client.post("/api/v1/browser/sessions/cleanup")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "cleaned"


# ==================== Tools List Tests ====================

class TestListTools:
    """列出工具测试"""

    def test_list_tools_success(self, test_client, mock_user):
        """测试成功列出工具"""
        from app.core.database import get_db
        from app.core.dependencies import get_current_user
        from app.main import app

        async def mock_get_current_user():
            return mock_user

        async def mock_get_db():
            yield MagicMock()

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_db] = mock_get_db

        try:
            with patch("app.api.v1.tools.get_global_registry") as mock_registry:
                mock_tool = MagicMock()
                mock_tool.name = "test-tool"
                mock_tool.description = "A test tool"
                mock_tool.parameters = {}
                mock_tool.risk_level.value = "LOW"
                mock_tool.requires_confirmation = False
                mock_tool.operation_categories = []

                registry = MagicMock()
                registry.__len__ = lambda self: 1
                registry.list_names.return_value = ["test-tool"]
                registry.get.return_value = mock_tool
                mock_registry.return_value = registry

                response = test_client.get("/api/v1/tools")

                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
        finally:
            app.dependency_overrides.clear()


class TestGetTool:
    """获取工具详情测试"""

    def test_get_tool_success(self, test_client, mock_user):
        """测试成功获取工具"""
        from app.core.database import get_db
        from app.core.dependencies import get_current_user
        from app.main import app

        async def mock_get_current_user():
            return mock_user

        async def mock_get_db():
            yield MagicMock()

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_db] = mock_get_db

        try:
            with patch("app.api.v1.tools.get_global_registry") as mock_registry:
                mock_tool = MagicMock()
                mock_tool.name = "file_read"
                mock_tool.description = "Read file content"
                mock_tool.parameters = {"path": {"type": "string"}}
                mock_tool.risk_level.value = "LOW"
                mock_tool.requires_confirmation = False
                mock_tool.operation_categories = []

                registry = MagicMock()
                registry.__len__ = lambda self: 1
                registry.has.return_value = True
                registry.get.return_value = mock_tool
                mock_registry.return_value = registry

                response = test_client.get("/api/v1/tools/file_read")

                assert response.status_code == 200
                data = response.json()
                assert data["name"] == "file_read"
        finally:
            app.dependency_overrides.clear()

    def test_get_tool_not_found(self, test_client, mock_user):
        """测试工具不存在"""
        from app.core.database import get_db
        from app.core.dependencies import get_current_user
        from app.main import app

        async def mock_get_current_user():
            return mock_user

        async def mock_get_db():
            yield MagicMock()

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_db] = mock_get_db

        try:
            with patch("app.api.v1.tools.get_global_registry") as mock_registry:
                registry = MagicMock()
                registry.__len__ = lambda self: 0
                registry.has.return_value = False
                mock_registry.return_value = registry

                response = test_client.get("/api/v1/tools/nonexistent")

                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()


class TestToolCategories:
    """工具分类测试"""

    def test_list_tool_categories(self, test_client, mock_user):
        """测试列出工具分类"""
        from app.core.database import get_db
        from app.core.dependencies import get_current_user
        from app.main import app

        async def mock_get_current_user():
            return mock_user

        async def mock_get_db():
            yield MagicMock()

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_db] = mock_get_db

        try:
            with patch("app.api.v1.tools.get_tool_categories") as mock_categories:
                mock_categories.return_value = {
                    "file_operations": ["file_read", "file_write"],
                    "web_operations": ["web_search", "web_scrape"]
                }

                response = test_client.get("/api/v1/tools/categories/list")

                assert response.status_code == 200
                data = response.json()
                assert "file_operations" in data or isinstance(data, dict)
        finally:
            app.dependency_overrides.clear()


class TestToolDescriptions:
    """工具描述测试"""

    def test_list_tool_descriptions(self, test_client, mock_user):
        """测试列出工具描述"""
        from app.core.database import get_db
        from app.core.dependencies import get_current_user
        from app.main import app

        async def mock_get_current_user():
            return mock_user

        async def mock_get_db():
            yield MagicMock()

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_db] = mock_get_db

        try:
            with patch("app.api.v1.tools.get_tool_descriptions") as mock_descriptions:
                mock_descriptions.return_value = {
                    "file_read": "Read content from a file",
                    "file_write": "Write content to a file"
                }

                response = test_client.get("/api/v1/tools/descriptions/list")

                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()


class TestRegisterTool:
    """注册工具测试"""

    def test_register_tool_not_implemented(self, test_client, mock_user):
        """测试注册工具（未实现）"""
        from app.core.database import get_db
        from app.core.dependencies import get_current_user
        from app.main import app

        async def mock_get_current_user():
            return mock_user

        async def mock_get_db():
            yield MagicMock()

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_db] = mock_get_db

        try:
            response = test_client.post(
                "/api/v1/tools/register",
                json={"name": "custom-tool", "description": "A custom tool"}
            )

            assert response.status_code == 501
        finally:
            app.dependency_overrides.clear()


# ==================== Health Check Tests ====================

class TestHealthCheck:
    """应用健康检查测试"""

    def test_health_check(self, test_client):
        """测试基础健康检查"""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_readiness_check(self, test_client):
        """测试就绪检查"""
        with patch("app.core.database.check_db_health") as mock_db, \
             patch("app.core.redis.check_redis_health") as mock_redis:

            mock_db.return_value = True
            mock_redis.return_value = True

            response = test_client.get("/readiness")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ["ready", "degraded"]
            assert "checks" in data


# ==================== Main ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
