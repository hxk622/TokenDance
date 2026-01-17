"""
Session API Tests

测试会话相关 API 端点：
- POST /api/v1/sessions - 创建会话
- GET /api/v1/sessions - 列出会话
- GET /api/v1/sessions/{id} - 获取会话详情
- PATCH /api/v1/sessions/{id} - 更新会话
- DELETE /api/v1/sessions/{id} - 删除会话
- POST /api/v1/sessions/{id}/complete - 完成会话
- GET /api/v1/sessions/{id}/messages - 获取会话消息
- GET /api/v1/sessions/{id}/artifacts - 获取会话 Artifacts
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ==================== Create Session Tests ====================

class TestCreateSession:
    """创建会话测试"""

    def test_create_session_success(self, test_client, mock_user, test_session_data, mock_session_response):
        """测试成功创建会话"""
        from app.main import app
        from app.core.dependencies import get_current_user, get_permission_service
        from app.api.v1.session import get_session_service
        
        async def mock_get_current_user():
            return mock_user
        
        mock_permission = AsyncMock()
        mock_permission.can_create_session = AsyncMock(return_value=True)
        
        async def mock_get_permission():
            return mock_permission
        
        mock_service = AsyncMock()
        mock_service.create_session = AsyncMock(return_value=mock_session_response)
        
        def mock_get_service(db=None):
            return mock_service
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_permission_service] = mock_get_permission
        app.dependency_overrides[get_session_service] = mock_get_service
        
        try:
            response = test_client.post(
                "/api/v1/sessions",
                json=test_session_data
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["title"] == mock_session_response["title"]
        finally:
            app.dependency_overrides.clear()

    def test_create_session_unauthorized(self, test_client, test_session_data):
        """测试未认证创建会话"""
        response = test_client.post(
            "/api/v1/sessions",
            json=test_session_data
        )
        
        assert response.status_code in [401, 403, 422]


# ==================== List Sessions Tests ====================

class TestListSessions:
    """列出会话测试"""

    def test_list_sessions_success(self, test_client, mock_user, mock_session_response):
        """测试成功列出会话"""
        from app.main import app
        from app.core.dependencies import get_current_user, get_permission_service
        from app.api.v1.session import get_session_service
        
        async def mock_get_current_user():
            return mock_user
        
        mock_permission = AsyncMock()
        mock_permission.check_workspace_access = AsyncMock(return_value=True)
        
        async def mock_get_permission():
            return mock_permission
        
        mock_service = AsyncMock()
        mock_service.list_sessions = AsyncMock(return_value={
            "items": [mock_session_response],
            "total": 1,
            "limit": 20,
            "offset": 0
        })
        
        def mock_get_service(db=None):
            return mock_service
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_permission_service] = mock_get_permission
        app.dependency_overrides[get_session_service] = mock_get_service
        
        try:
            response = test_client.get("/api/v1/sessions?workspace_id=test-workspace-id")
            
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
        finally:
            app.dependency_overrides.clear()

    def test_list_sessions_missing_workspace_id(self, test_client, mock_user):
        """测试缺少 workspace_id 参数"""
        from app.main import app
        from app.core.dependencies import get_current_user
        
        async def mock_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        try:
            response = test_client.get("/api/v1/sessions")
            
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()


# ==================== Get Session Tests ====================

class TestGetSession:
    """获取会话详情测试"""

    def test_get_session_success(self, test_client, mock_user, mock_session_response):
        """测试成功获取会话"""
        from app.main import app
        from app.core.dependencies import get_current_user, get_permission_service
        from app.api.v1.session import get_session_service
        
        async def mock_get_current_user():
            return mock_user
        
        mock_permission = AsyncMock()
        mock_permission.check_session_access = AsyncMock(return_value=True)
        
        async def mock_get_permission():
            return mock_permission
        
        mock_service = AsyncMock()
        mock_service.get_session = AsyncMock(return_value=mock_session_response)
        
        def mock_get_service(db=None):
            return mock_service
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_permission_service] = mock_get_permission
        app.dependency_overrides[get_session_service] = mock_get_service
        
        try:
            response = test_client.get("/api/v1/sessions/test-session-id")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == mock_session_response["id"]
        finally:
            app.dependency_overrides.clear()

    def test_get_session_not_found(self, test_client, mock_user):
        """测试会话不存在"""
        from app.main import app
        from app.core.dependencies import get_current_user, get_permission_service
        from app.api.v1.session import get_session_service
        
        async def mock_get_current_user():
            return mock_user
        
        mock_permission = AsyncMock()
        mock_permission.check_session_access = AsyncMock(return_value=True)
        
        async def mock_get_permission():
            return mock_permission
        
        mock_service = AsyncMock()
        mock_service.get_session = AsyncMock(return_value=None)
        
        def mock_get_service(db=None):
            return mock_service
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_permission_service] = mock_get_permission
        app.dependency_overrides[get_session_service] = mock_get_service
        
        try:
            response = test_client.get("/api/v1/sessions/nonexistent-id")
            
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()


# ==================== Update Session Tests ====================

class TestUpdateSession:
    """更新会话测试"""

    def test_update_session_success(self, test_client, mock_user, mock_session_response):
        """测试成功更新会话"""
        from app.main import app
        from app.core.dependencies import get_current_user, get_permission_service
        from app.api.v1.session import get_session_service
        
        async def mock_get_current_user():
            return mock_user
        
        mock_permission = AsyncMock()
        mock_permission.check_session_access = AsyncMock(return_value=True)
        
        async def mock_get_permission():
            return mock_permission
        
        updated_response = {**mock_session_response, "title": "Updated Session"}
        mock_service = AsyncMock()
        mock_service.update_session = AsyncMock(return_value=updated_response)
        
        def mock_get_service(db=None):
            return mock_service
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_permission_service] = mock_get_permission
        app.dependency_overrides[get_session_service] = mock_get_service
        
        try:
            response = test_client.patch(
                "/api/v1/sessions/test-session-id",
                json={"title": "Updated Session"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Updated Session"
        finally:
            app.dependency_overrides.clear()


# ==================== Delete Session Tests ====================

class TestDeleteSession:
    """删除会话测试"""

    def test_delete_session_success(self, test_client, mock_user):
        """测试成功删除会话"""
        from app.main import app
        from app.core.dependencies import get_current_user, get_permission_service
        from app.api.v1.session import get_session_service
        
        async def mock_get_current_user():
            return mock_user
        
        mock_permission = AsyncMock()
        mock_permission.check_session_access = AsyncMock(return_value=True)
        
        async def mock_get_permission():
            return mock_permission
        
        mock_service = AsyncMock()
        mock_service.delete_session = AsyncMock(return_value=True)
        
        def mock_get_service(db=None):
            return mock_service
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_permission_service] = mock_get_permission
        app.dependency_overrides[get_session_service] = mock_get_service
        
        try:
            response = test_client.delete("/api/v1/sessions/test-session-id")
            
            assert response.status_code == 204
        finally:
            app.dependency_overrides.clear()


# ==================== Complete Session Tests ====================

class TestCompleteSession:
    """完成会话测试"""

    def test_complete_session_success(self, test_client, mock_user, mock_session_response):
        """测试成功完成会话"""
        from app.main import app
        from app.core.dependencies import get_current_user, get_permission_service
        from app.api.v1.session import get_session_service
        
        async def mock_get_current_user():
            return mock_user
        
        mock_permission = AsyncMock()
        mock_permission.check_session_access = AsyncMock(return_value=True)
        
        async def mock_get_permission():
            return mock_permission
        
        completed_response = {**mock_session_response, "status": "completed"}
        mock_service = AsyncMock()
        mock_service.complete_session = AsyncMock(return_value=completed_response)
        
        def mock_get_service(db=None):
            return mock_service
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_permission_service] = mock_get_permission
        app.dependency_overrides[get_session_service] = mock_get_service
        
        try:
            response = test_client.post("/api/v1/sessions/test-session-id/complete")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
        finally:
            app.dependency_overrides.clear()


# ==================== Get Session Messages Tests ====================

class TestGetSessionMessages:
    """获取会话消息测试"""

    def test_get_session_messages_success(self, test_client, mock_user, mock_session_response):
        """测试成功获取会话消息"""
        from app.main import app
        from app.core.dependencies import get_current_user, get_permission_service
        from app.api.v1.session import get_session_service
        
        async def mock_get_current_user():
            return mock_user
        
        mock_permission = AsyncMock()
        mock_permission.check_session_access = AsyncMock(return_value=True)
        
        async def mock_get_permission():
            return mock_permission
        
        mock_service = AsyncMock()
        mock_service.get_session = AsyncMock(return_value=mock_session_response)
        mock_service.get_session_messages = AsyncMock(return_value={
            "items": [
                {"id": "msg-1", "role": "user", "content": "Hello"},
                {"id": "msg-2", "role": "assistant", "content": "Hi there!"}
            ],
            "total": 2
        })
        
        def mock_get_service(db=None):
            return mock_service
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_permission_service] = mock_get_permission
        app.dependency_overrides[get_session_service] = mock_get_service
        
        try:
            response = test_client.get("/api/v1/sessions/test-session-id/messages")
            
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert len(data["items"]) == 2
        finally:
            app.dependency_overrides.clear()


# ==================== Get Session Artifacts Tests ====================

class TestGetSessionArtifacts:
    """获取会话 Artifacts 测试"""

    def test_get_session_artifacts_success(self, test_client, mock_user, mock_session_response):
        """测试成功获取会话 Artifacts"""
        from app.main import app
        from app.core.dependencies import get_current_user, get_permission_service
        from app.api.v1.session import get_session_service
        
        async def mock_get_current_user():
            return mock_user
        
        mock_permission = AsyncMock()
        mock_permission.check_session_access = AsyncMock(return_value=True)
        
        async def mock_get_permission():
            return mock_permission
        
        mock_service = AsyncMock()
        mock_service.get_session = AsyncMock(return_value=mock_session_response)
        mock_service.get_session_artifacts = AsyncMock(return_value={
            "items": [
                {"id": "artifact-1", "type": "file", "name": "output.txt"}
            ],
            "total": 1
        })
        
        def mock_get_service(db=None):
            return mock_service
        
        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_permission_service] = mock_get_permission
        app.dependency_overrides[get_session_service] = mock_get_service
        
        try:
            response = test_client.get("/api/v1/sessions/test-session-id/artifacts")
            
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
        finally:
            app.dependency_overrides.clear()


# ==================== Main ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
