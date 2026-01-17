"""
Workspace API Tests

测试工作空间相关 API 端点：
- POST /api/v1/workspaces - 创建工作空间
- GET /api/v1/workspaces - 列出工作空间
- GET /api/v1/workspaces/{id} - 获取工作空间详情
- PATCH /api/v1/workspaces/{id} - 更新工作空间
- DELETE /api/v1/workspaces/{id} - 删除工作空间
- GET /api/v1/workspaces/{id}/sessions - 获取工作空间会话
"""

from unittest.mock import AsyncMock

import pytest

# ==================== Create Workspace Tests ====================

class TestCreateWorkspace:
    """创建工作空间测试"""

    def test_create_workspace_success(
        self, test_client, mock_user, test_workspace_data, mock_workspace_response
    ):
        """测试成功创建工作空间"""
        from app.api.v1.workspace import get_workspace_service
        from app.core.dependencies import get_current_user, get_permission_service
        from app.main import app

        # Mock dependencies
        async def mock_get_current_user():
            return mock_user

        mock_permission = AsyncMock()
        mock_permission.can_create_workspace = AsyncMock(return_value=True)

        async def mock_get_permission():
            return mock_permission

        mock_service = AsyncMock()
        mock_service.create_workspace = AsyncMock(return_value=mock_workspace_response)

        def mock_get_service(db=None):
            return mock_service

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_permission_service] = mock_get_permission
        app.dependency_overrides[get_workspace_service] = mock_get_service

        try:
            response = test_client.post(
                "/api/v1/workspaces",
                json=test_workspace_data
            )

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == mock_workspace_response["name"]
        finally:
            app.dependency_overrides.clear()

    def test_create_workspace_unauthorized(self, test_client, test_workspace_data):
        """测试未认证创建工作空间"""
        response = test_client.post(
            "/api/v1/workspaces",
            json=test_workspace_data
        )

        assert response.status_code in [401, 403, 422]

    def test_create_workspace_forbidden(self, test_client, mock_user, test_workspace_data):
        """测试无权限创建工作空间"""
        from app.core.dependencies import get_current_user, get_permission_service
        from app.main import app
        from app.services.permission_service import PermissionError

        async def mock_get_current_user():
            return mock_user

        mock_permission = AsyncMock()
        mock_permission.can_create_workspace = AsyncMock(
            side_effect=PermissionError("Not allowed")
        )

        async def mock_get_permission():
            return mock_permission

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_permission_service] = mock_get_permission

        try:
            response = test_client.post(
                "/api/v1/workspaces",
                json=test_workspace_data
            )

            assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()


# ==================== List Workspaces Tests ====================

class TestListWorkspaces:
    """列出工作空间测试"""

    def test_list_workspaces_success(self, test_client, mock_user, mock_workspace_response):
        """测试成功列出工作空间"""
        from app.api.v1.workspace import get_workspace_service
        from app.core.dependencies import get_current_user
        from app.main import app

        async def mock_get_current_user():
            return mock_user

        mock_service = AsyncMock()
        mock_service.list_workspaces = AsyncMock(return_value={
            "items": [mock_workspace_response],
            "total": 1,
            "limit": 20,
            "offset": 0
        })

        def mock_get_service(db=None):
            return mock_service

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_workspace_service] = mock_get_service

        try:
            response = test_client.get("/api/v1/workspaces")

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert len(data["items"]) == 1
        finally:
            app.dependency_overrides.clear()

    def test_list_workspaces_with_pagination(self, test_client, mock_user):
        """测试分页列出工作空间"""
        from app.api.v1.workspace import get_workspace_service
        from app.core.dependencies import get_current_user
        from app.main import app

        async def mock_get_current_user():
            return mock_user

        mock_service = AsyncMock()
        mock_service.list_workspaces = AsyncMock(return_value={
            "items": [],
            "total": 0,
            "limit": 10,
            "offset": 5
        })

        def mock_get_service(db=None):
            return mock_service

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_workspace_service] = mock_get_service

        try:
            response = test_client.get("/api/v1/workspaces?limit=10&offset=5")

            assert response.status_code == 200
            mock_service.list_workspaces.assert_called_once()
        finally:
            app.dependency_overrides.clear()


# ==================== Get Workspace Tests ====================

class TestGetWorkspace:
    """获取工作空间详情测试"""

    def test_get_workspace_success(self, test_client, mock_user, mock_workspace_response):
        """测试成功获取工作空间"""
        from app.api.v1.workspace import get_workspace_service
        from app.core.dependencies import get_current_user, get_permission_service
        from app.main import app

        async def mock_get_current_user():
            return mock_user

        mock_permission = AsyncMock()
        mock_permission.check_workspace_access = AsyncMock(return_value=True)

        async def mock_get_permission():
            return mock_permission

        mock_service = AsyncMock()
        mock_service.get_workspace = AsyncMock(return_value=mock_workspace_response)

        def mock_get_service(db=None):
            return mock_service

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_permission_service] = mock_get_permission
        app.dependency_overrides[get_workspace_service] = mock_get_service

        try:
            response = test_client.get("/api/v1/workspaces/test-workspace-id")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == mock_workspace_response["id"]
        finally:
            app.dependency_overrides.clear()

    def test_get_workspace_not_found(self, test_client, mock_user):
        """测试工作空间不存在"""
        from app.api.v1.workspace import get_workspace_service
        from app.core.dependencies import get_current_user, get_permission_service
        from app.main import app

        async def mock_get_current_user():
            return mock_user

        mock_permission = AsyncMock()
        mock_permission.check_workspace_access = AsyncMock(return_value=True)

        async def mock_get_permission():
            return mock_permission

        mock_service = AsyncMock()
        mock_service.get_workspace = AsyncMock(return_value=None)

        def mock_get_service(db=None):
            return mock_service

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_permission_service] = mock_get_permission
        app.dependency_overrides[get_workspace_service] = mock_get_service

        try:
            response = test_client.get("/api/v1/workspaces/nonexistent-id")

            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()


# ==================== Update Workspace Tests ====================

class TestUpdateWorkspace:
    """更新工作空间测试"""

    def test_update_workspace_success(self, test_client, mock_user, mock_workspace_response):
        """测试成功更新工作空间"""
        from app.api.v1.workspace import get_workspace_service
        from app.core.dependencies import get_current_user, get_permission_service
        from app.main import app

        async def mock_get_current_user():
            return mock_user

        mock_permission = AsyncMock()
        mock_permission.check_workspace_access = AsyncMock(return_value=True)

        async def mock_get_permission():
            return mock_permission

        updated_response = {**mock_workspace_response, "name": "Updated Workspace"}
        mock_service = AsyncMock()
        mock_service.update_workspace = AsyncMock(return_value=updated_response)

        def mock_get_service(db=None):
            return mock_service

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_permission_service] = mock_get_permission
        app.dependency_overrides[get_workspace_service] = mock_get_service

        try:
            response = test_client.patch(
                "/api/v1/workspaces/test-workspace-id",
                json={"name": "Updated Workspace"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Workspace"
        finally:
            app.dependency_overrides.clear()


# ==================== Delete Workspace Tests ====================

class TestDeleteWorkspace:
    """删除工作空间测试"""

    def test_delete_workspace_success(self, test_client, mock_user):
        """测试成功删除工作空间"""
        from app.api.v1.workspace import get_workspace_service
        from app.core.dependencies import get_current_user, get_permission_service
        from app.main import app

        async def mock_get_current_user():
            return mock_user

        mock_permission = AsyncMock()
        mock_permission.check_workspace_access = AsyncMock(return_value=True)

        async def mock_get_permission():
            return mock_permission

        mock_service = AsyncMock()
        mock_service.delete_workspace = AsyncMock(return_value=True)

        def mock_get_service(db=None):
            return mock_service

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_permission_service] = mock_get_permission
        app.dependency_overrides[get_workspace_service] = mock_get_service

        try:
            response = test_client.delete("/api/v1/workspaces/test-workspace-id")

            assert response.status_code == 204
        finally:
            app.dependency_overrides.clear()

    def test_delete_workspace_not_found(self, test_client, mock_user):
        """测试删除不存在的工作空间"""
        from app.api.v1.workspace import get_workspace_service
        from app.core.dependencies import get_current_user, get_permission_service
        from app.main import app

        async def mock_get_current_user():
            return mock_user

        mock_permission = AsyncMock()
        mock_permission.check_workspace_access = AsyncMock(return_value=True)

        async def mock_get_permission():
            return mock_permission

        mock_service = AsyncMock()
        mock_service.delete_workspace = AsyncMock(return_value=False)

        def mock_get_service(db=None):
            return mock_service

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_permission_service] = mock_get_permission
        app.dependency_overrides[get_workspace_service] = mock_get_service

        try:
            response = test_client.delete("/api/v1/workspaces/nonexistent-id")

            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()


# ==================== Get Workspace Sessions Tests ====================

class TestGetWorkspaceSessions:
    """获取工作空间会话测试"""

    def test_get_workspace_sessions_success(self, test_client, mock_user, mock_session_response):
        """测试成功获取工作空间会话"""
        from app.api.v1.workspace import get_workspace_service
        from app.core.dependencies import get_current_user, get_permission_service
        from app.main import app

        async def mock_get_current_user():
            return mock_user

        mock_permission = AsyncMock()
        mock_permission.check_workspace_access = AsyncMock(return_value=True)

        async def mock_get_permission():
            return mock_permission

        mock_service = AsyncMock()
        mock_service.get_workspace_sessions = AsyncMock(return_value={
            "items": [mock_session_response],
            "total": 1
        })

        def mock_get_service(db=None):
            return mock_service

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_permission_service] = mock_get_permission
        app.dependency_overrides[get_workspace_service] = mock_get_service

        try:
            response = test_client.get("/api/v1/workspaces/test-workspace-id/sessions")

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
        finally:
            app.dependency_overrides.clear()


# ==================== Main ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
