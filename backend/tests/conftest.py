"""
Shared pytest fixtures for backend tests.

提供测试所需的公共 fixtures，包括：
- 测试客户端
- Mock 数据库会话
- Mock 用户认证
- 测试数据工厂
"""

import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch
from typing import AsyncGenerator, Generator

import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport


# ==================== 环境配置 ====================

# 设置测试环境变量
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")


# ==================== 基础 Fixtures ====================

@pytest.fixture(scope="session")
def anyio_backend():
    """指定 async 后端为 asyncio"""
    return "asyncio"


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """创建同步测试客户端"""
    from app.main import app
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """创建异步测试客户端"""
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ==================== Mock 数据库 Fixtures ====================

@pytest.fixture
def mock_db_session():
    """创建 Mock 数据库会话"""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def mock_get_db(mock_db_session):
    """Mock get_db 依赖"""
    async def _get_db():
        yield mock_db_session
    return _get_db


# ==================== Mock 用户认证 Fixtures ====================

@pytest.fixture
def mock_user():
    """创建 Mock 用户对象"""
    user = MagicMock()
    user.id = "test-user-id"
    user.email = "test@example.com"
    user.username = "testuser"
    user.is_active = True
    user.is_superuser = False
    user.created_at = "2024-01-01T00:00:00"
    return user


@pytest.fixture
def mock_superuser():
    """创建 Mock 超级用户"""
    user = MagicMock()
    user.id = "super-user-id"
    user.email = "admin@example.com"
    user.username = "admin"
    user.is_active = True
    user.is_superuser = True
    user.created_at = "2024-01-01T00:00:00"
    return user


@pytest.fixture
def mock_current_user(mock_user):
    """Mock get_current_user 依赖"""
    return mock_user


@pytest.fixture
def override_auth_deps(mock_user, mock_db_session):
    """覆盖认证相关的依赖"""
    from app.main import app
    from app.core.dependencies import get_current_user
    from app.core.database import get_db
    
    async def mock_get_current_user():
        return mock_user
    
    async def mock_get_db_override():
        yield mock_db_session
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_db] = mock_get_db_override
    
    yield
    
    # 清理
    app.dependency_overrides.clear()


# ==================== 测试数据 Fixtures ====================

@pytest.fixture
def test_workspace_data():
    """测试工作空间数据"""
    return {
        "name": "Test Workspace",
        "slug": "test-workspace",
        "description": "A workspace for testing",
        "workspace_type": "personal",
    }


@pytest.fixture
def test_session_data():
    """测试会话数据"""
    return {
        "workspace_id": "test-workspace-id",
        "user_id": "test-user-id",
        "title": "Test Session",
    }


@pytest.fixture
def test_message_data():
    """测试消息数据"""
    return {
        "content": "Hello, this is a test message",
        "stream": False,
    }


@pytest.fixture
def test_user_register_data():
    """测试用户注册数据"""
    return {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "SecurePass123!",
    }


@pytest.fixture
def test_user_login_data():
    """测试用户登录数据"""
    return {
        "email": "test@example.com",
        "password": "TestPass123!",
    }


# ==================== Mock Service Fixtures ====================

@pytest.fixture
def mock_auth_service():
    """Mock 认证服务"""
    service = AsyncMock()
    service.register = AsyncMock()
    service.login = AsyncMock()
    service.refresh_access_token = AsyncMock()
    service.login_with_wechat = AsyncMock()
    service.login_with_gmail = AsyncMock()
    return service


@pytest.fixture
def mock_session_service():
    """Mock 会话服务"""
    service = AsyncMock()
    service.create_session = AsyncMock()
    service.get_session = AsyncMock()
    service.list_sessions = AsyncMock()
    service.update_session = AsyncMock()
    service.delete_session = AsyncMock()
    service.complete_session = AsyncMock()
    service.get_session_messages = AsyncMock()
    service.get_session_artifacts = AsyncMock()
    return service


@pytest.fixture
def mock_workspace_service():
    """Mock 工作空间服务"""
    service = AsyncMock()
    service.create_workspace = AsyncMock()
    service.get_workspace = AsyncMock()
    service.list_workspaces = AsyncMock()
    service.update_workspace = AsyncMock()
    service.delete_workspace = AsyncMock()
    service.get_workspace_sessions = AsyncMock()
    return service


@pytest.fixture
def mock_permission_service():
    """Mock 权限服务"""
    service = AsyncMock()
    service.can_create_workspace = AsyncMock(return_value=True)
    service.can_create_session = AsyncMock(return_value=True)
    service.check_workspace_access = AsyncMock(return_value=True)
    service.check_session_access = AsyncMock(return_value=True)
    return service


# ==================== API 响应 Mock ====================

@pytest.fixture
def mock_workspace_response():
    """Mock 工作空间响应"""
    return {
        "id": "test-workspace-id",
        "name": "Test Workspace",
        "slug": "test-workspace",
        "description": "A workspace for testing",
        "workspace_type": "personal",
        "owner_id": "test-user-id",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }


@pytest.fixture
def mock_session_response():
    """Mock 会话响应"""
    return {
        "id": "test-session-id",
        "workspace_id": "test-workspace-id",
        "user_id": "test-user-id",
        "title": "Test Session",
        "status": "active",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }


@pytest.fixture
def mock_token_response():
    """Mock Token 响应"""
    return {
        "access_token": "test-access-token",
        "refresh_token": "test-refresh-token",
        "token_type": "bearer",
    }


# ==================== 清理 Fixtures ====================

@pytest.fixture(autouse=True)
def cleanup_dependency_overrides():
    """每个测试后自动清理依赖覆盖"""
    yield
    from app.main import app
    app.dependency_overrides.clear()


# ==================== Markers ====================

def pytest_configure(config):
    """注册自定义 markers"""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "api: marks tests as API tests")
