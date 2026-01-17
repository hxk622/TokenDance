"""
Auth API Tests

测试认证相关 API 端点：
- POST /api/v1/auth/register - 用户注册
- POST /api/v1/auth/login - 用户登录
- POST /api/v1/auth/refresh - 刷新 Token
- GET /api/v1/auth/me - 获取当前用户信息
- OAuth 相关端点（WeChat, Gmail）
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


def create_mock_user(email: str, username: str):
    """创建符合 UserResponse schema 的 mock 用户"""
    user = MagicMock()
    user.id = uuid4()
    user.email = email
    user.username = username
    user.display_name = username
    user.avatar_url = None
    user.auth_provider = "email_password"
    user.is_active = True
    user.is_verified = True
    user.email_verified = True
    user.created_at = datetime.now()
    user.updated_at = datetime.now()
    user.last_login_at = None
    user.personal_quota = {}
    user.usage_stats = {}
    return user


def create_mock_tokens():
    """创建 mock tokens"""
    tokens = MagicMock()
    tokens.access_token = "mock-access-token-12345"
    tokens.refresh_token = "mock-refresh-token-67890"
    tokens.token_type = "bearer"
    return tokens


# ==================== Register Tests ====================

class TestRegister:
    """用户注册测试"""

    def test_register_success(self, test_client, test_user_register_data):
        """测试成功注册用户"""
        from app.main import app
        from app.core.dependencies import get_auth_service
        
        mock_user = create_mock_user(
            email=test_user_register_data["email"],
            username=test_user_register_data["username"]
        )
        mock_tokens = create_mock_tokens()
        
        mock_service = AsyncMock()
        mock_service.register = AsyncMock(return_value=(mock_user, mock_tokens))
        
        async def mock_get_auth_service():
            return mock_service
        
        app.dependency_overrides[get_auth_service] = mock_get_auth_service
        
        try:
            response = test_client.post(
                "/api/v1/auth/register",
                json=test_user_register_data
            )
            
            assert response.status_code == 201
            data = response.json()
            assert "user" in data
            assert "tokens" in data
            assert data["user"]["email"] == test_user_register_data["email"]
        finally:
            app.dependency_overrides.clear()

    def test_register_duplicate_email(self, test_client, test_user_register_data):
        """测试重复邮箱注册失败"""
        from app.main import app
        from app.core.dependencies import get_auth_service
        
        mock_service = AsyncMock()
        mock_service.register = AsyncMock(side_effect=ValueError("Email already registered"))
        
        async def mock_get_auth_service():
            return mock_service
        
        app.dependency_overrides[get_auth_service] = mock_get_auth_service
        
        try:
            response = test_client.post(
                "/api/v1/auth/register",
                json=test_user_register_data
            )
            
            assert response.status_code == 400
            assert "already" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    def test_register_invalid_email(self, test_client):
        """测试无效邮箱格式"""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "username": "testuser",
                "password": "TestPass123!"
            }
        )
        
        assert response.status_code == 422

    def test_register_missing_fields(self, test_client):
        """测试缺少必填字段"""
        response = test_client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com"}
        )
        
        assert response.status_code == 422


# ==================== Login Tests ====================

class TestLogin:
    """用户登录测试"""

    def test_login_success(self, test_client, test_user_login_data):
        """测试成功登录"""
        from app.main import app
        from app.core.dependencies import get_auth_service
        
        mock_user = create_mock_user(
            email=test_user_login_data["email"],
            username="testuser"
        )
        mock_tokens = create_mock_tokens()
        
        mock_service = AsyncMock()
        mock_service.login = AsyncMock(return_value=(mock_user, mock_tokens))
        
        async def mock_get_auth_service():
            return mock_service
        
        app.dependency_overrides[get_auth_service] = mock_get_auth_service
        
        try:
            response = test_client.post(
                "/api/v1/auth/login",
                json=test_user_login_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "user" in data
            assert "tokens" in data
        finally:
            app.dependency_overrides.clear()

    def test_login_invalid_credentials(self, test_client, test_user_login_data):
        """测试无效凭证登录失败"""
        from app.main import app
        from app.core.dependencies import get_auth_service
        
        mock_service = AsyncMock()
        mock_service.login = AsyncMock(side_effect=ValueError("Invalid credentials"))
        
        async def mock_get_auth_service():
            return mock_service
        
        app.dependency_overrides[get_auth_service] = mock_get_auth_service
        
        try:
            response = test_client.post(
                "/api/v1/auth/login",
                json=test_user_login_data
            )
            
            assert response.status_code == 401
        finally:
            app.dependency_overrides.clear()

    def test_login_missing_password(self, test_client):
        """测试缺少密码"""
        response = test_client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com"}
        )
        
        assert response.status_code == 422


# ==================== Refresh Token Tests ====================

class TestRefreshToken:
    """Token 刷新测试"""

    def test_refresh_token_success(self, test_client):
        """测试成功刷新 Token"""
        from app.main import app
        from app.core.dependencies import get_auth_service
        
        mock_tokens = create_mock_tokens()
        mock_tokens.access_token = "new-mock-access-token"
        mock_tokens.refresh_token = "new-mock-refresh-token"
        
        mock_service = AsyncMock()
        mock_service.refresh_access_token = AsyncMock(return_value=mock_tokens)
        
        async def mock_get_auth_service():
            return mock_service
        
        app.dependency_overrides[get_auth_service] = mock_get_auth_service
        
        try:
            response = test_client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "valid-refresh-token-xyz"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
        finally:
            app.dependency_overrides.clear()

    def test_refresh_token_invalid(self, test_client):
        """测试无效 Refresh Token"""
        from app.main import app
        from app.core.dependencies import get_auth_service
        
        mock_service = AsyncMock()
        mock_service.refresh_access_token = AsyncMock(
            side_effect=ValueError("Invalid refresh token")
        )
        
        async def mock_get_auth_service():
            return mock_service
        
        app.dependency_overrides[get_auth_service] = mock_get_auth_service
        
        try:
            response = test_client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "invalid-token-abc"}
            )
            
            assert response.status_code == 401
        finally:
            app.dependency_overrides.clear()


# ==================== Get Current User Tests ====================

class TestGetCurrentUser:
    """获取当前用户信息测试"""

    def test_get_current_user_success(self, test_client):
        """测试成功获取当前用户"""
        from app.main import app
        from app.core.dependencies import get_current_user
        
        mock_user = create_mock_user(
            email="currentuser@example.com",
            username="currentuser"
        )
        
        async def mock_get_current_user_override():
            return mock_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user_override
        
        try:
            response = test_client.get("/api/v1/auth/me")
            
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "currentuser@example.com"
        finally:
            app.dependency_overrides.clear()

    def test_get_current_user_unauthorized(self, test_client):
        """测试未认证访问"""
        # 不设置依赖覆盖，使用默认认证
        response = test_client.get("/api/v1/auth/me")
        
        # 应该返回 401 或 403
        assert response.status_code in [401, 403, 422]


# ==================== OAuth Tests ====================

class TestWeChatOAuth:
    """WeChat OAuth 测试"""

    def test_wechat_authorize(self, test_client):
        """测试获取 WeChat 授权 URL"""
        with patch("app.services.wechat_oauth_service.WeChatOAuthService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_authorization_url.return_value = "https://wechat.com/oauth/authorize"
            mock_service_class.return_value = mock_service
            
            response = test_client.get("/api/v1/auth/wechat/authorize")
            
            assert response.status_code == 200
            assert "authorization_url" in response.json()

    def test_wechat_callback_success(self, test_client):
        """测试 WeChat 回调成功"""
        from app.main import app
        from app.core.dependencies import get_auth_service
        
        mock_user = create_mock_user(
            email="wechat@example.com",
            username="wechatuser"
        )
        mock_user.auth_provider = "wechat"
        mock_tokens = create_mock_tokens()
        
        mock_service = AsyncMock()
        mock_service.login_with_wechat = AsyncMock(return_value=(mock_user, mock_tokens))
        
        async def mock_get_auth_service():
            return mock_service
        
        app.dependency_overrides[get_auth_service] = mock_get_auth_service
        
        try:
            response = test_client.post(
                "/api/v1/auth/wechat/callback",
                json={"code": "wechat-auth-code-xyz"}
            )
            
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()


class TestGmailOAuth:
    """Gmail OAuth 测试"""

    def test_gmail_authorize(self, test_client):
        """测试获取 Gmail 授权 URL"""
        with patch("app.services.gmail_oauth_service.GmailOAuthService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_authorization_url.return_value = "https://accounts.google.com/oauth/authorize"
            mock_service_class.return_value = mock_service
            
            response = test_client.get("/api/v1/auth/gmail/authorize")
            
            assert response.status_code == 200
            assert "authorization_url" in response.json()

    def test_gmail_callback_success(self, test_client):
        """测试 Gmail 回调成功"""
        from app.main import app
        from app.core.dependencies import get_auth_service
        
        mock_user = create_mock_user(
            email="gmail@example.com",
            username="gmailuser"
        )
        mock_user.auth_provider = "gmail"
        mock_tokens = create_mock_tokens()
        
        mock_service = AsyncMock()
        mock_service.login_with_gmail = AsyncMock(return_value=(mock_user, mock_tokens))
        
        async def mock_get_auth_service():
            return mock_service
        
        app.dependency_overrides[get_auth_service] = mock_get_auth_service
        
        try:
            response = test_client.post(
                "/api/v1/auth/gmail/callback",
                json={"code": "gmail-auth-code-xyz"}
            )
            
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()


# ==================== Main ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
