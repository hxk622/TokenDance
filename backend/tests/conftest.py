"""
Shared pytest fixtures for backend tests.

提供测试所需的公共 fixtures，包括：
- 测试客户端
- Mock 数据库会话
- Mock 用户认证
- 测试数据工厂
"""

import fnmatch
import os
import time
from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

# ==================== 环境配置 ====================

RUN_INTEGRATION_TESTS = os.getenv("RUN_INTEGRATION_TESTS")

# 设置测试环境变量（仅限非集成测试）
if not RUN_INTEGRATION_TESTS:
    os.environ.setdefault("ENVIRONMENT", "development")
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
    os.environ.setdefault("DISABLE_REDIS", "true")
    os.environ.setdefault("FINANCIAL_DATA_MODE", "mock")
else:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
        try:
            with open(env_path, "r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip("'").strip('"')
                    os.environ.setdefault(key, value)
        except FileNotFoundError:
            pass
    os.environ.setdefault("HF_HUB_DISABLE_SSL_VERIFICATION", "1")


# ==================== Fake Redis ====================

class FakeRedis:
    """Simple in-memory async Redis replacement for tests."""

    def __init__(self) -> None:
        self._data: dict[str, object] = {}
        self._hashes: dict[str, dict[str, str]] = {}
        self._zsets: dict[str, dict[str, float]] = {}
        self._expiry: dict[str, float] = {}

    def reset(self) -> None:
        self._data.clear()
        self._hashes.clear()
        self._zsets.clear()
        self._expiry.clear()

    def _purge_expired(self) -> None:
        now = time.time()
        expired = [key for key, ts in self._expiry.items() if ts <= now]
        for key in expired:
            self._data.pop(key, None)
            self._hashes.pop(key, None)
            self._zsets.pop(key, None)
            self._expiry.pop(key, None)

    async def ping(self) -> bool:
        return True

    async def aclose(self) -> None:
        return None

    async def get(self, key: str):
        self._purge_expired()
        return self._data.get(key)

    async def set(self, key: str, value: object):
        self._purge_expired()
        self._data[key] = value
        return True

    async def setex(self, key: str, ttl: int, value: object):
        self._data[key] = value
        self._expiry[key] = time.time() + ttl
        return True

    async def exists(self, key: str) -> int:
        self._purge_expired()
        return 1 if (key in self._data or key in self._hashes or key in self._zsets) else 0

    async def delete(self, key: str) -> int:
        self._purge_expired()
        removed = 0
        if key in self._data:
            del self._data[key]
            removed = 1
        if key in self._hashes:
            del self._hashes[key]
            removed = 1
        if key in self._zsets:
            del self._zsets[key]
            removed = 1
        self._expiry.pop(key, None)
        return removed

    async def incr(self, key: str) -> int:
        self._purge_expired()
        current = int(self._data.get(key, 0) or 0)
        current += 1
        self._data[key] = current
        return current

    async def expire(self, key: str, ttl: int) -> bool:
        self._expiry[key] = time.time() + ttl
        return True

    async def hset(self, key: str, mapping: dict[str, str]):
        self._purge_expired()
        self._hashes.setdefault(key, {}).update(mapping)
        return True

    async def hgetall(self, key: str) -> dict[str, str]:
        self._purge_expired()
        return dict(self._hashes.get(key, {}))

    async def scan_iter(self, match: str | None = None):
        self._purge_expired()
        keys = set(self._data) | set(self._hashes) | set(self._zsets)
        for key in keys:
            if match is None or fnmatch.fnmatch(key, match):
                yield key

    async def zadd(self, key: str, mapping: dict[str, float]):
        self._purge_expired()
        zset = self._zsets.setdefault(key, {})
        added = 0
        for member, score in mapping.items():
            if member not in zset:
                added += 1
            zset[member] = float(score)
        return added

    async def zcard(self, key: str) -> int:
        self._purge_expired()
        return len(self._zsets.get(key, {}))

    async def zremrangebyrank(self, key: str, start: int, end: int) -> int:
        self._purge_expired()
        zset = self._zsets.get(key)
        if not zset:
            return 0
        sorted_members = sorted(zset.items(), key=lambda item: (item[1], item[0]))
        if end < 0:
            end = len(sorted_members) + end
        if start < 0:
            start = len(sorted_members) + start
        to_remove = sorted_members[start:end + 1]
        for member, _ in to_remove:
            zset.pop(member, None)
        return len(to_remove)

    async def zrangebyscore(
        self,
        key: str,
        min_score: str | float,
        max_score: str | float,
        start: int = 0,
        num: int | None = None,
    ) -> list[str]:
        self._purge_expired()
        zset = self._zsets.get(key, {})
        if not zset:
            return []

        def parse_score(value):
            if isinstance(value, (int, float)):
                return float(value), False
            if isinstance(value, str) and value.startswith("("):
                return float(value[1:]), True
            if value == "-inf":
                return float("-inf"), False
            if value == "+inf":
                return float("inf"), False
            return float(value), False

        min_val, min_exclusive = parse_score(min_score)
        max_val, max_exclusive = parse_score(max_score)

        def in_range(score: float) -> bool:
            if min_exclusive:
                if score <= min_val:
                    return False
            else:
                if score < min_val:
                    return False
            if max_exclusive:
                if score >= max_val:
                    return False
            else:
                if score > max_val:
                    return False
            return True

        filtered = [(member, score) for member, score in zset.items() if in_range(score)]
        filtered.sort(key=lambda item: (item[1], item[0]))
        sliced = filtered[start:] if num is None else filtered[start:start + num]
        return [member for member, _ in sliced]

    async def zrange(self, key: str, start: int, end: int) -> list[str]:
        self._purge_expired()
        zset = self._zsets.get(key, {})
        if not zset:
            return []
        sorted_members = sorted(zset.items(), key=lambda item: (item[1], item[0]))
        if end < 0:
            end = len(sorted_members) + end
        if start < 0:
            start = len(sorted_members) + start
        return [member for member, _ in sorted_members[start:end + 1]]


@pytest.fixture(scope="session", autouse=True)
def _init_fake_redis():
    """Initialize a shared FakeRedis client for all tests."""
    if RUN_INTEGRATION_TESTS:
        yield
        return
    from app.core import redis as redis_module

    redis_module.redis_client = FakeRedis()
    yield
    redis_module.redis_client = None


@pytest.fixture(autouse=True)
def _reset_fake_redis():
    """Reset FakeRedis state between tests."""
    if RUN_INTEGRATION_TESTS:
        yield
        return
    from app.core import redis as redis_module

    client = redis_module.redis_client
    if client is None:
        redis_module.redis_client = FakeRedis()
    elif hasattr(client, "reset"):
        client.reset()
    yield


# ==================== 基础 Fixtures ====================

@pytest.fixture(scope="session")
def anyio_backend():
    """指定 async 后端为 asyncio"""
    return "asyncio"


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """创建同步测试客户端"""
    from app.main import app
    if RUN_INTEGRATION_TESTS:
        with TestClient(app) as client:
            yield client
        return
    from app.core.redis import get_redis
    from app.core import redis as redis_module

    fake_redis = FakeRedis()
    redis_module.redis_client = fake_redis

    async def override_get_redis():
        yield fake_redis

    app.dependency_overrides[get_redis] = override_get_redis

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.pop(get_redis, None)
    redis_module.redis_client = None


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """创建异步测试客户端"""
    from app.main import app
    if RUN_INTEGRATION_TESTS:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
        return
    from app.core.redis import get_redis
    from app.core import redis as redis_module

    fake_redis = FakeRedis()
    redis_module.redis_client = fake_redis

    async def override_get_redis():
        yield fake_redis

    app.dependency_overrides[get_redis] = override_get_redis
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.pop(get_redis, None)
    redis_module.redis_client = None


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
    from app.core.database import get_db
    from app.core.dependencies import get_current_user
    from app.main import app

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
        "team_id": None,
        "filesystem_path": "/data/users/test-user-id/workspaces/test-workspace-id",
        "settings": {
            "llm_model": "claude-3-5-sonnet-20241022",
            "enable_auto_save": True,
            "max_context_tokens": 128000,
            "compression_threshold": 10240,
        },
        "stats": {
            "total_tasks": 0,
            "completed_tasks": 0,
            "active_agents": 0,
            "storage_used_mb": 0,
            "monthly_tokens_used": 0,
        },
        "session_count": 0,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
        "last_accessed_at": None,
    }


@pytest.fixture
def mock_session_response():
    """Mock 会话响应"""
    return {
        "id": "test-session-id",
        "workspace_id": "test-workspace-id",
        "title": "Test Session",
        "status": "active",
        "skill_id": None,
        "total_tokens_used": 0,
        "message_count": 0,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
        "completed_at": None,
    }


@pytest.fixture
def mock_token_response():
    """Mock Token 响应"""
    return {
        "access_token": "test-access-token",
        "refresh_token": "test-refresh-token",
        "token_type": "bearer",
    }


@pytest.fixture
def mock_project_response():
    """Mock Project 响应"""
    return {
        "id": "test-project-id",
        "workspace_id": "test-workspace-id",
        "title": "Test Project",
        "intent": "测试项目",
        "description": "A test project",
        "project_type": "research",
        "status": "draft",
        "context": {
            "goals": [],
            "decisions": [],
            "failures": [],
            "findings": [],
            "constraints": [],
            "tags": [],
        },
        "settings": {
            "llm_model": "claude-3-5-sonnet-20241022",
            "max_iterations": 10,
            "auto_archive": True,
            "allow_code_execution": False,
        },
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }


# ==================== Integration Test Fixtures ====================
# 这些 fixture 用于集成测试，需要真实数据库
# 单元测试应使用上面的 mock fixtures

@pytest.fixture
def test_workspace_id():
    """测试用的 workspace ID

    Note: 这是一个假的 ID，用于 mock 测试。
    集成测试应该创建真实的 workspace。
    """
    return "test-workspace-id"


@pytest.fixture
def test_project(mock_project_response):
    """测试用的 project 数据

    Note: 这是 mock 数据，用于单元测试。
    集成测试应该创建真实的 project。
    """
    return mock_project_response


# ==================== 清理 Fixtures ====================

@pytest.fixture(autouse=True)
def cleanup_dependency_overrides():
    """每个测试后自动清理依赖覆盖"""
    yield
    from app.main import app
    app.dependency_overrides.clear()


# ==================== Integration Database Fixtures ====================
# 这些 fixture 用于集成测试，会创建真实的数据库表

@pytest_asyncio.fixture
async def db_with_tables():
    """创建带有表结构的内存数据库 session

    此 fixture 会：
    1. 导入所有 models 以注册到 Base.metadata
    2. 创建所有表
    3. 提供 database session
    4. 测试结束后清理
    """
    from sqlalchemy import event
    from sqlalchemy.exc import CircularDependencyError
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.core.database import Base

    # Import all models to register them with Base.metadata
    import app.models  # noqa: F401

    # 创建内存数据库引擎
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # 启用 SQLite 外键支持
    @event.listens_for(test_engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # 创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 创建 session factory
    test_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with test_session_maker() as session:
        yield session

    # 清理表
    async with test_engine.begin() as conn:
        await conn.exec_driver_sql("PRAGMA foreign_keys=OFF")
        try:
            await conn.run_sync(Base.metadata.drop_all)
        except CircularDependencyError:
            # In-memory SQLite teardown can ignore FK cycles; DB will be disposed anyway.
            pass

    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_with_tables):
    """提供统一的数据库 session fixture (兼容历史测试用例)."""
    yield db_with_tables

@pytest_asyncio.fixture
async def db_user(db_session):
    """创建测试用户 (真实数据库对象)."""
    from app.models.user import User

    user = User(
        id="test-user-id",
        email="test@example.com",
        username="testuser",
        password_hash="hashed_password",
        is_active=True,
        is_verified=True,
        email_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def db_workspace(db_session, db_user):
    """创建测试工作空间 (真实数据库对象)."""
    from app.models.workspace import Workspace

    workspace = Workspace(
        id="test-workspace-id",
        name="Test Workspace",
        slug="test-workspace",
        owner_id=db_user.id,
        filesystem_path=f"/data/users/{db_user.id}/workspaces/test-workspace-id",
    )
    db_session.add(workspace)
    await db_session.commit()
    return workspace


@pytest_asyncio.fixture
async def db_project(db_session, db_workspace):
    """创建测试 Project (真实数据库对象)."""
    from app.models.project import Project, ProjectType

    project = Project(
        id="test-project-id",
        workspace_id=db_workspace.id,
        intent="Test project intent",
        title="Test Project",
        project_type=ProjectType.RESEARCH,
    )
    db_session.add(project)
    await db_session.commit()
    return project


@pytest.fixture
def test_client_with_db(db_with_tables):
    """带有真实数据库的测试客户端

    用于集成测试，会用测试数据库覆盖 get_db 依赖
    """
    from app.core.database import get_db
    from app.main import app

    async def override_get_db():
        yield db_with_tables

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


# ==================== Markers ====================

def pytest_configure(config):
    """注册自定义 markers"""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "api: marks tests as API tests")
