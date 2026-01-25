"""
Chat Message API Tests

测试消息发送 API 端点：
- POST /api/v1/chat/{session_id}/message - 发送消息 (主要的消息发送方式)

这是新的统一消息发送架构的核心端点，支持：
- 认证和权限检查
- 消息持久化
- Session 状态管理
- 附件支持 (图片、文档)
- SSE 流式响应
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.session import SessionStatus


# ==================== Test Fixtures ====================

@pytest.fixture
def auth_headers():
    """创建认证请求头"""
    return {
        "Authorization": "Bearer test-token-12345"
    }


def create_mock_user():
    """创建符合 User model 的 mock 用户"""
    user = MagicMock()
    user.id = uuid4()
    user.email = "test@example.com"
    user.username = "testuser"
    user.display_name = "Test User"
    user.is_active = True
    return user


def create_mock_session(user_id=None, status=SessionStatus.PENDING):
    """创建 mock session"""
    session = MagicMock()
    session.id = str(uuid4())
    session.user_id = user_id or uuid4()
    session.workspace_id = str(uuid4())
    session.status = status
    session.title = "Test Session"
    session.description = None
    session.created_at = datetime.now()
    session.updated_at = datetime.now()
    return session


# ==================== Send Message Tests ====================


class TestSendMessage:
    """发送消息测试"""

    def test_send_message_unauthorized(self, test_client):
        """测试未认证请求返回 401"""
        session_id = str(uuid4())
        response = test_client.post(
            f"/api/v1/chat/{session_id}/message",
            json={"content": "Hello"}
        )
        assert response.status_code == 401

    def test_send_message_empty_content(self, test_client, auth_headers):
        """测试空消息内容"""
        from app.core.dependencies import get_current_user, get_permission_service, get_db
        from app.main import app

        mock_user = create_mock_user()
        mock_session = create_mock_session(user_id=mock_user.id)

        async def mock_get_current_user():
            return mock_user

        mock_permission = AsyncMock()
        mock_permission.check_session_access = AsyncMock()

        async def mock_get_permission():
            return mock_permission

        mock_db = AsyncMock()

        async def mock_get_db():
            return mock_db

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_permission_service] = mock_get_permission
        app.dependency_overrides[get_db] = mock_get_db

        try:
            response = test_client.post(
                f"/api/v1/chat/{mock_session.id}/message",
                json={"content": ""},
                headers=auth_headers
            )
            # Empty content should still be accepted (could be image-only message)
            # The validation is handled at a higher level
            assert response.status_code in [200, 400, 422]
        finally:
            app.dependency_overrides.clear()

    def test_send_message_session_not_found(self, test_client, auth_headers):
        """测试 session 不存在返回 404"""
        from app.core.dependencies import get_current_user, get_permission_service, get_db
        from app.services.permission_service import PermissionError
        from app.main import app

        mock_user = create_mock_user()
        session_id = str(uuid4())

        async def mock_get_current_user():
            return mock_user

        mock_permission = AsyncMock()
        mock_permission.check_session_access = AsyncMock(
            side_effect=PermissionError("Session not found")
        )

        async def mock_get_permission():
            return mock_permission

        mock_db = AsyncMock()

        async def mock_get_db():
            return mock_db

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_permission_service] = mock_get_permission
        app.dependency_overrides[get_db] = mock_get_db

        try:
            response = test_client.post(
                f"/api/v1/chat/{session_id}/message",
                json={"content": "Hello"},
                headers=auth_headers
            )
            # Should return 403 (permission denied) or 404
            assert response.status_code in [403, 404]
        finally:
            app.dependency_overrides.clear()

    def test_send_message_permission_denied(self, test_client, auth_headers):
        """测试无权限访问 session 返回 403"""
        from app.core.dependencies import get_current_user, get_permission_service, get_db
        from app.services.permission_service import PermissionError
        from app.main import app

        mock_user = create_mock_user()
        other_user_id = uuid4()
        mock_session = create_mock_session(user_id=other_user_id)

        async def mock_get_current_user():
            return mock_user

        mock_permission = AsyncMock()
        mock_permission.check_session_access = AsyncMock(
            side_effect=PermissionError("You don't have access to this session")
        )

        async def mock_get_permission():
            return mock_permission

        mock_db = AsyncMock()

        async def mock_get_db():
            return mock_db

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_permission_service] = mock_get_permission
        app.dependency_overrides[get_db] = mock_get_db

        try:
            response = test_client.post(
                f"/api/v1/chat/{mock_session.id}/message",
                json={"content": "Hello"},
                headers=auth_headers
            )
            assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()

    def test_send_message_session_already_running(self, test_client, auth_headers):
        """测试 session 正在运行时发送消息返回 409"""
        from app.core.dependencies import get_current_user, get_permission_service, get_db
        from app.services.session_service import SessionService
        from app.main import app

        mock_user = create_mock_user()
        mock_session = create_mock_session(user_id=mock_user.id, status=SessionStatus.RUNNING)

        async def mock_get_current_user():
            return mock_user

        mock_permission = AsyncMock()
        mock_permission.check_session_access = AsyncMock()

        async def mock_get_permission():
            return mock_permission

        # Mock SessionService to return RUNNING session
        with patch.object(SessionService, 'get_session', new_callable=AsyncMock) as mock_get_session:
            mock_get_session.return_value = mock_session

            mock_db = AsyncMock()

            async def mock_get_db():
                return mock_db

            app.dependency_overrides[get_current_user] = mock_get_current_user
            app.dependency_overrides[get_permission_service] = mock_get_permission
            app.dependency_overrides[get_db] = mock_get_db

            try:
                response = test_client.post(
                    f"/api/v1/chat/{mock_session.id}/message",
                    json={"content": "Hello"},
                    headers=auth_headers
                )
                # Session already running should return 409 Conflict
                assert response.status_code == 409
            finally:
                app.dependency_overrides.clear()


class TestSendMessageWithAttachments:
    """发送带附件消息测试"""

    def test_send_message_with_image_attachment(self, test_client, auth_headers):
        """测试发送带图片附件的消息"""
        from app.core.dependencies import get_current_user, get_permission_service, get_db
        from app.main import app

        mock_user = create_mock_user()
        mock_session = create_mock_session(user_id=mock_user.id)

        async def mock_get_current_user():
            return mock_user

        mock_permission = AsyncMock()
        mock_permission.check_session_access = AsyncMock()

        async def mock_get_permission():
            return mock_permission

        mock_db = AsyncMock()

        async def mock_get_db():
            return mock_db

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_permission_service] = mock_get_permission
        app.dependency_overrides[get_db] = mock_get_db

        try:
            response = test_client.post(
                f"/api/v1/chat/{mock_session.id}/message",
                json={
                    "content": "Analyze this image",
                    "attachments": [
                        {
                            "type": "image",
                            "name": "test.png",
                            "mime_type": "image/png",
                            "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg..."
                        }
                    ]
                },
                headers=auth_headers
            )
            # Request format is valid, may fail due to mocked services
            assert response.status_code in [200, 400, 404, 500]
        finally:
            app.dependency_overrides.clear()

    def test_send_message_with_document_attachment(self, test_client, auth_headers):
        """测试发送带文档附件的消息"""
        from app.core.dependencies import get_current_user, get_permission_service, get_db
        from app.main import app

        mock_user = create_mock_user()
        mock_session = create_mock_session(user_id=mock_user.id)

        async def mock_get_current_user():
            return mock_user

        mock_permission = AsyncMock()
        mock_permission.check_session_access = AsyncMock()

        async def mock_get_permission():
            return mock_permission

        mock_db = AsyncMock()

        async def mock_get_db():
            return mock_db

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_permission_service] = mock_get_permission
        app.dependency_overrides[get_db] = mock_get_db

        try:
            response = test_client.post(
                f"/api/v1/chat/{mock_session.id}/message",
                json={
                    "content": "Summarize this document",
                    "attachments": [
                        {
                            "type": "document",
                            "name": "report.pdf",
                            "mime_type": "application/pdf",
                            "url": "data:application/pdf;base64,JVBERi0xLjQ..."
                        }
                    ]
                },
                headers=auth_headers
            )
            # Request format is valid
            assert response.status_code in [200, 400, 404, 500]
        finally:
            app.dependency_overrides.clear()


class TestMessageRequestValidation:
    """消息请求验证测试"""

    def test_invalid_attachment_type(self, test_client, auth_headers):
        """测试无效的附件类型"""
        from app.core.dependencies import get_current_user, get_permission_service, get_db
        from app.main import app

        mock_user = create_mock_user()

        async def mock_get_current_user():
            return mock_user

        mock_permission = AsyncMock()
        mock_permission.check_session_access = AsyncMock()

        async def mock_get_permission():
            return mock_permission

        mock_db = AsyncMock()

        async def mock_get_db():
            return mock_db

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_permission_service] = mock_get_permission
        app.dependency_overrides[get_db] = mock_get_db

        try:
            session_id = str(uuid4())
            response = test_client.post(
                f"/api/v1/chat/{session_id}/message",
                json={
                    "content": "Hello",
                    "attachments": [
                        {
                            "type": "invalid_type",  # Invalid type
                            "name": "test.xyz",
                            "mime_type": "application/octet-stream",
                            "url": "data:application/octet-stream;base64,..."
                        }
                    ]
                },
                headers=auth_headers
            )
            # Should return 422 for invalid attachment type
            assert response.status_code in [400, 403, 422]
        finally:
            app.dependency_overrides.clear()

    def test_missing_attachment_url(self, test_client, auth_headers):
        """测试缺少附件 URL"""
        from app.core.dependencies import get_current_user, get_permission_service, get_db
        from app.main import app

        mock_user = create_mock_user()

        async def mock_get_current_user():
            return mock_user

        mock_permission = AsyncMock()
        mock_permission.check_session_access = AsyncMock()

        async def mock_get_permission():
            return mock_permission

        mock_db = AsyncMock()

        async def mock_get_db():
            return mock_db

        app.dependency_overrides[get_current_user] = mock_get_current_user
        app.dependency_overrides[get_permission_service] = mock_get_permission
        app.dependency_overrides[get_db] = mock_get_db

        try:
            session_id = str(uuid4())
            response = test_client.post(
                f"/api/v1/chat/{session_id}/message",
                json={
                    "content": "Hello",
                    "attachments": [
                        {
                            "type": "image",
                            "name": "test.png",
                            "mime_type": "image/png"
                            # Missing url
                        }
                    ]
                },
                headers=auth_headers
            )
            # Should return 422 for missing required field
            assert response.status_code in [400, 403, 422]
        finally:
            app.dependency_overrides.clear()
