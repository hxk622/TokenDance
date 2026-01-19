"""
AIOSandboxPool 单元测试

重点测试并发访问控制和 SessionState 状态机。
"""

import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.sandbox.exceptions import ConcurrentAccessError
from app.sandbox.pool import AIOSandboxPool, PoolConfig, PooledSandbox, SessionState
from app.sandbox.workspace import AgentWorkspace, WorkspaceConfig


class TestSessionState:
    """SessionState 枚举测试"""

    def test_values(self):
        """检查所有值"""
        assert SessionState.IDLE.value == "idle"
        assert SessionState.ACQUIRING.value == "acquiring"
        assert SessionState.BUSY.value == "busy"


class TestPooledSandbox:
    """PooledSandbox 测试"""

    def test_default_state(self):
        """默认状态"""
        mock_sandbox = MagicMock()
        pooled = PooledSandbox(
            sandbox=mock_sandbox,
            session_id="test_session",
        )

        assert pooled.state == SessionState.IDLE
        assert pooled.use_count == 0
        assert isinstance(pooled.created_at, datetime)

    def test_custom_state(self):
        """自定义状态"""
        mock_sandbox = MagicMock()
        pooled = PooledSandbox(
            sandbox=mock_sandbox,
            session_id="test_session",
            state=SessionState.BUSY,
            use_count=5,
        )

        assert pooled.state == SessionState.BUSY
        assert pooled.use_count == 5


class TestPoolConfig:
    """PoolConfig 测试"""

    def test_default_values(self):
        """默认配置"""
        config = PoolConfig()

        assert config.max_instances == 10
        assert config.min_instances == 2
        assert config.idle_timeout_seconds == 300
        assert config.max_use_count == 100

    def test_custom_values(self):
        """自定义配置"""
        config = PoolConfig(
            max_instances=5,
            min_instances=1,
            idle_timeout_seconds=60,
            max_use_count=50,
        )

        assert config.max_instances == 5
        assert config.min_instances == 1


class TestAIOSandboxPool:
    """AIOSandboxPool 测试"""

    @pytest.fixture
    def pool_config(self) -> PoolConfig:
        """池配置"""
        return PoolConfig(
            max_instances=3,
            min_instances=0,  # 测试时不预热
            idle_timeout_seconds=60,
        )

    @pytest.fixture
    def pool(self, pool_config: PoolConfig) -> AIOSandboxPool:
        """创建沙箱池"""
        return AIOSandboxPool(pool_config)

    # ==================== 基本功能测试 ====================

    def test_init(self, pool: AIOSandboxPool):
        """初始化"""
        assert pool.config.max_instances == 3
        assert len(pool._session_map) == 0
        assert len(pool._idle_queue) == 0
        assert not pool._running

    @pytest.mark.asyncio
    async def test_acquire_busy_session_raises(self, pool: AIOSandboxPool):
        """获取已占用的会话抛出 ConcurrentAccessError"""
        # 直接放置一个 BUSY 状态的 session
        mock_sandbox = MagicMock()
        pooled = PooledSandbox(
            sandbox=mock_sandbox,
            session_id="test_session",
            state=SessionState.BUSY,
        )
        pool._session_map["test_session"] = pooled

        # 再次获取应该抛出异常
        with pytest.raises(ConcurrentAccessError, match="正在被使用"):
            await pool.acquire("test_session")

    @pytest.mark.asyncio
    async def test_acquire_acquiring_session_raises(self, pool: AIOSandboxPool):
        """获取正在初始化的会话抛出 ConcurrentAccessError"""
        # 直接放置一个 ACQUIRING 状态的 session
        pooled = PooledSandbox(
            sandbox=None,  # type: ignore
            session_id="test_session",
            state=SessionState.ACQUIRING,
        )
        pool._session_map["test_session"] = pooled

        # 再次获取应该抛出异常
        with pytest.raises(ConcurrentAccessError, match="正在初始化"):
            await pool.acquire("test_session")

    @pytest.mark.asyncio
    async def test_acquire_idle_session_reuses(self, pool: AIOSandboxPool):
        """获取空闲会话时复用"""
        # 放置一个 IDLE 状态的 session
        mock_sandbox = MagicMock()
        pooled = PooledSandbox(
            sandbox=mock_sandbox,
            session_id="test_session",
            state=SessionState.IDLE,
            use_count=0,
        )
        pool._session_map["test_session"] = pooled

        # 获取应该复用
        sandbox = await pool.acquire("test_session")

        assert sandbox == mock_sandbox
        assert pool._session_map["test_session"].state == SessionState.BUSY
        assert pool._session_map["test_session"].use_count == 1

    @pytest.mark.asyncio
    async def test_release_returns_to_idle(self, pool: AIOSandboxPool):
        """释放会话后返回 idle 队列"""
        # 放置一个 BUSY 状态的 session
        mock_sandbox = MagicMock()
        pooled = PooledSandbox(
            sandbox=mock_sandbox,
            session_id="test_session",
            state=SessionState.BUSY,
        )
        pool._session_map["test_session"] = pooled

        # 释放
        await pool.release("test_session")

        # 应该移到 idle 队列
        assert "test_session" in pool._idle_queue
        assert pool._idle_queue["test_session"].state == SessionState.IDLE

    @pytest.mark.asyncio
    async def test_release_nonexistent_session_no_error(self, pool: AIOSandboxPool):
        """释放不存在的会话不抛出异常"""
        # 不应该抛出异常
        await pool.release("nonexistent_session")

    @pytest.mark.asyncio
    async def test_stop_cleans_up(self, pool: AIOSandboxPool):
        """停止池时清理所有会话"""
        # 放置一些 session
        mock_sandbox = MagicMock()
        mock_sandbox.cleanup = AsyncMock()
        pooled = PooledSandbox(
            sandbox=mock_sandbox,
            session_id="test_session",
            state=SessionState.BUSY,
        )
        pool._session_map["test_session"] = pooled
        pool._running = True

        # 停止
        with patch.object(pool, "_destroy", new_callable=AsyncMock) as mock_destroy:
            await pool.stop()

            assert not pool._running
            assert len(pool._session_map) == 0
