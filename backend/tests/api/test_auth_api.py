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
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


# ==================== Register Tests ====================

class TestRegister:
    """用户注册测试"""

    def test_register_success(self, test_client, test_user_register_data):
        """测试成功注册用户"""
        with patch("app.api.v1.auth.get_auth_service") as mock_get_service:
            # Setup mock
            mock_service = AsyncMock()
            mock_user = MagicMock()
            mock_user.id = "new-user-id"
            mock_user.email = test_user_register_data["email"]
            mock_user.username = test_user_register_data["username"]
            mock_user.is_active = True
            mock_user.is_superuser = False
            mock_user.created_at = "2024-01-01T00:00:00"
            
            mock_tokens = MagicMock()
            mock_tokens.access_token = "test-access-token"
            mock_tokens.refresh_token = "test-refresh-token"
            mock_tokens.token_type = "bearer"
            
            mock_service.register.return_value = (mock_user, mock_tokens)
            mock_get_service.return_value = mock_service
            
            # Execute
            response = test_client.post(
                "/api/v1/auth/register",
                json=test_user_register_data
            )
            
            # Verify
            assert response.status_code == 201
            data = response.json()
            assert "user" in data
            assert "tokens" in data
            assert data["user"]["email"] == test_user_register_data["email"]
            assert data["tokens"]["access_token"] == "test-access-token"

    def test_register_duplicate_email(self, test_client, test_user_register_data):
        """测试重复邮箱注册失败"""
        with patch("app.api.v1.auth.get_auth_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.register.side_effect = ValueError("Email already exists")
            mock_get_service.return_value = mock_service
            
            response = test_client.post(
                "/api/v1/auth/register",
                json=test_user_register_data
            )
            
            assert response.status_code == 400
            assert "Email already exists" in response.json()["detail"]

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
        with patch("app.api.v1.auth.get_auth_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_user = MagicMock()
            mock_user.id = "test-user-id"
            mock_user.email = test_user_login_data["email"]
            mock_user.username = "testuser"
            mock_user.is_active = True
            mock_user.is_superuser = False
            mock_user.created_at = "2024-01-01T00:00:00"
            
            mock_tokens = MagicMock()
            mock_tokens.access_token = "test-access-token"
            mock_tokens.refresh_token = "test-refresh-token"
            mock_tokens.token_type = "bearer"
            
            mock_service.login.return_value = (mock_user, mock_tokens)
            mock_get_service.return_value = mock_service
            
            response = test_client.post(
                "/api/v1/auth/login",
                json=test_user_login_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "user" in data
            assert "tokens" in data

    def test_login_invalid_credentials(self, test_client, test_user_login_data):
        """测试无效凭证登录失败"""
        with patch("app.api.v1.auth.get_auth_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.login.side_effect = ValueError("Invalid credentials")
            mock_get_service.return_value = mock_service
            
            response = test_client.post(
                "/api/v1/auth/login",
                json=test_user_login_data
            )
            
            assert response.status_code == 401

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
        with patch("app.api.v1.auth.get_auth_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_tokens = MagicMock()
            mock_tokens.access_token = "new-access-token"
            mock_tokens.refresh_token = "new-refresh-token"
            mock_tokens.token_type = "bearer"
            
            mock_service.refresh_access_token.return_value = mock_tokens
            mock_get_service.return_value = mock_service
            
            response = test_client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "valid-refresh-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["access_token"] == "new-access-token"

    def test_refresh_token_invalid(self, test_client):
        """测试无效 Refresh Token"""
        with patch("app.api.v1.auth.get_auth_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.refresh_access_token.side_effect = ValueError("Invalid refresh token")
            mock_get_service.return_value = mock_service
            
            response = test_client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "invalid-token"}
            )
            
            assert response.status_code == 401


# ==================== Get Current User Tests ====================

class TestGetCurrentUser:
    """获取当前用户信息测试"""

    def test_get_current_user_success(self, test_client, mock_user):
        """测试成功获取当前用户"""
        from app.main import app
        from app.core.dependencies import get_current_user
        
        async def mock_get_current_user_override():
            return mock_user
        
        app.dependency_overrides[get_current_user] = mock_get_current_user_override
        
        try:
            response = test_client.get("/api/v1/auth/me")
            
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == mock_user.email
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
        with patch("app.api.v1.auth.WeChatOAuthService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_authorization_url.return_value = "https://wechat.com/oauth/authorize"
            mock_service_class.return_value = mock_service
            
            response = test_client.get("/api/v1/auth/wechat/authorize")
            
            assert response.status_code == 200
            assert "authorization_url" in response.json()

    def test_wechat_callback_success(self, test_client):
        """测试 WeChat 回调成功"""
        with patch("app.api.v1.auth.get_auth_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_user = MagicMock()
            mock_user.id = "wechat-user-id"
            mock_user.email = "wechat@example.com"
            mock_user.username = "wechatuser"
            mock_user.is_active = True
            mock_user.is_superuser = False
            mock_user.created_at = "2024-01-01T00:00:00"
            
            mock_tokens = MagicMock()
            mock_tokens.access_token = "wechat-access-token"
            mock_tokens.refresh_token = "wechat-refresh-token"
            mock_tokens.token_type = "bearer"
            
            mock_service.login_with_wechat.return_value = (mock_user, mock_tokens)
            mock_get_service.return_value = mock_service
            
            response = test_client.post(
                "/api/v1/auth/wechat/callback",
                json={"code": "wechat-auth-code"}
            )
            
            assert response.status_code == 200


class TestGmailOAuth:
    """Gmail OAuth 测试"""

    def test_gmail_authorize(self, test_client):
        """测试获取 Gmail 授权 URL"""
        with patch("app.api.v1.auth.GmailOAuthService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_authorization_url.return_value = "https://accounts.google.com/oauth/authorize"
            mock_service_class.return_value = mock_service
            
            response = test_client.get("/api/v1/auth/gmail/authorize")
            
            assert response.status_code == 200
            assert "authorization_url" in response.json()

    def test_gmail_callback_success(self, test_client):
        """测试 Gmail 回调成功"""
        with patch("app.api.v1.auth.get_auth_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_user = MagicMock()
            mock_user.id = "gmail-user-id"
            mock_user.email = "gmail@example.com"
            mock_user.username = "gmailuser"
            mock_user.is_active = True
            mock_user.is_superuser = False
            mock_user.created_at = "2024-01-01T00:00:00"
            
            mock_tokens = MagicMock()
            mock_tokens.access_token = "gmail-access-token"
            mock_tokens.refresh_token = "gmail-refresh-token"
            mock_tokens.token_type = "bearer"
            
            mock_service.login_with_gmail.return_value = (mock_user, mock_tokens)
            mock_get_service.return_value = mock_service
            
            response = test_client.post(
                "/api/v1/auth/gmail/callback",
                json={"code": "gmail-auth-code"}
            )
            
            assert response.status_code == 200


# ==================== Main ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
