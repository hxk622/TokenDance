"""
AIOSandboxPool 单元测试

重点测试并发访问控制。
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.sandbox.exceptions import ConcurrentAccessError
from app.sandbox.pool import AIOSandboxPool, PoolConfig, PooledSandbox, SessionState


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

    @pytest.mark.asyncio
    async def test_acquire_new_session(self, pool: AIOSandboxPool):
        """获取新会话"""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={"session_id": "session_123", "status": "ready"}
            )
            mock_post.return_value.__aenter__.return_value = mock_response

            session_id = await pool.acquire_session("user_1")

            assert session_id == "session_123"
            assert pool._sessions["user_1"].session_id == "session_123"
            assert pool._sessions["user_1"].state == SessionState.ACTIVE

    @pytest.mark.asyncio
    async def test_release_session(self, pool: AIOSandboxPool):
        """释放会话"""
        # 先获取会话
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={"session_id": "session_123", "status": "ready"}
            )
            mock_post.return_value.__aenter__.return_value = mock_response

            session_id = await pool.acquire_session("user_1")

        # 释放会话
        with patch("aiohttp.ClientSession.delete") as mock_delete:
            mock_delete_response = AsyncMock()
            mock_delete_response.status = 200
            mock_delete.return_value.__aenter__.return_value = mock_delete_response

            await pool.release_session("user_1")

            assert "user_1" not in pool._sessions

    @pytest.mark.asyncio
    async def test_get_session_info(self, pool: AIOSandboxPool):
        """获取会话信息"""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={"session_id": "session_123", "status": "ready"}
            )
            mock_post.return_value.__aenter__.return_value = mock_response

            await pool.acquire_session("user_1")

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_info_response = AsyncMock()
            mock_info_response.status = 200
            mock_info_response.json = AsyncMock(
                return_value={"session_id": "session_123", "status": "active"}
            )
            mock_get.return_value.__aenter__.return_value = mock_info_response

            info = await pool.get_session_info("user_1")

            assert info["session_id"] == "session_123"
            assert info["status"] == "active"

    # ==================== 并发访问控制测试 ====================

    @pytest.mark.asyncio
    async def test_concurrent_acquire_same_user(self, pool: AIOSandboxPool):
        """同一用户并发获取会话"""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={"session_id": "session_123", "status": "ready"}
            )
            mock_post.return_value.__aenter__.return_value = mock_response

            # 第一次获取成功
            session_id = await pool.acquire_session("user_1")
            assert session_id == "session_123"

            # 第二次获取应该抛出异常（已经有会话在使用）
            with pytest.raises(ConcurrentAccessError, match="已经在使用"):
                await pool.acquire_session("user_1")

    @pytest.mark.asyncio
    async def test_concurrent_acquire_different_users(self, pool: AIOSandboxPool):
        """不同用户并发获取会话"""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response1 = AsyncMock()
            mock_response1.status = 200
            mock_response1.json = AsyncMock(
                return_value={"session_id": "session_123", "status": "ready"}
            )

            mock_response2 = AsyncMock()
            mock_response2.status = 200
            mock_response2.json = AsyncMock(
                return_value={"session_id": "session_456", "status": "ready"}
            )

            mock_post.return_value.__aenter__.side_effect = [
                mock_response1,
                mock_response2,
            ]

            # 不同用户可以同时获取会话
            session1 = await pool.acquire_session("user_1")
            session2 = await pool.acquire_session("user_2")

            assert session1 == "session_123"
            assert session2 == "session_456"
            assert len(pool._sessions) == 2

    @pytest.mark.asyncio
    async def test_reacquire_after_release(self, pool: AIOSandboxPool):
        """释放后重新获取"""
        with patch("aiohttp.ClientSession.post") as mock_post, patch(
            "aiohttp.ClientSession.delete"
        ) as mock_delete:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={"session_id": "session_123", "status": "ready"}
            )
            mock_post.return_value.__aenter__.return_value = mock_response

            mock_delete_response = AsyncMock()
            mock_delete_response.status = 200
            mock_delete.return_value.__aenter__.return_value = mock_delete_response

            # 获取
            session_id1 = await pool.acquire_session("user_1")
            assert session_id1 == "session_123"

            # 释放
            await pool.release_session("user_1")

            # 重新获取
            session_id2 = await pool.acquire_session("user_1")
            assert session_id2 == "session_123"

    # ==================== 池大小限制测试 ====================

    @pytest.mark.asyncio
    async def test_pool_size_limit(self, pool: AIOSandboxPool):
        """池大小限制"""
        with patch("aiohttp.ClientSession.post") as mock_post:

            async def mock_post_response(*args, **kwargs):
                mock_response = AsyncMock()
                mock_response.status = 200
                user_id = kwargs.get("json", {}).get("user_id", "default")
                mock_response.json = AsyncMock(
                    return_value={
                        "session_id": f"session_{user_id}",
                        "status": "ready",
                    }
                )
                return mock_response

            mock_post.return_value.__aenter__.side_effect = mock_post_response

            # 获取最大数量的会话
            for i in range(pool.config.max_pool_size):
                await pool.acquire_session(f"user_{i}")

            # 超过限制应该抛出异常
            with pytest.raises(
                SandboxNotAvailableError, match="已达到最大池大小"
            ):
                await pool.acquire_session("user_overflow")

    # ==================== 会话状态测试 ====================

    @pytest.mark.asyncio
    async def test_session_state_transitions(self, pool: AIOSandboxPool):
        """会话状态转换"""
        with patch("aiohttp.ClientSession.post") as mock_post, patch(
            "aiohttp.ClientSession.delete"
        ) as mock_delete:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={"session_id": "session_123", "status": "ready"}
            )
            mock_post.return_value.__aenter__.return_value = mock_response

            mock_delete_response = AsyncMock()
            mock_delete_response.status = 200
            mock_delete.return_value.__aenter__.return_value = mock_delete_response

            # IDLE -> ACQUIRING
            assert "user_1" not in pool._sessions

            # ACQUIRING -> ACTIVE
            await pool.acquire_session("user_1")
            assert pool._sessions["user_1"].state == SessionState.ACTIVE

            # ACTIVE -> IDLE (after release)
            await pool.release_session("user_1")
            assert "user_1" not in pool._sessions

    @pytest.mark.asyncio
    async def test_get_pool_status(self, pool: AIOSandboxPool):
        """获取池状态"""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={"session_id": "session_123", "status": "ready"}
            )
            mock_post.return_value.__aenter__.return_value = mock_response

            # 初始状态
            status = pool.get_pool_status()
            assert status["active_sessions"] == 0
            assert status["available_slots"] == 3

            # 获取一个会话
            await pool.acquire_session("user_1")

            status = pool.get_pool_status()
            assert status["active_sessions"] == 1
            assert status["available_slots"] == 2

    # ==================== 错误处理测试 ====================

    @pytest.mark.asyncio
    async def test_release_nonexistent_session(self, pool: AIOSandboxPool):
        """释放不存在的会话"""
        # 不应该抛出异常
        await pool.release_session("nonexistent_user")

    @pytest.mark.asyncio
    async def test_get_info_nonexistent_session(self, pool: AIOSandboxPool):
        """获取不存在的会话信息"""
        with pytest.raises(SandboxNotAvailableError, match="会话不存在"):
            await pool.get_session_info("nonexistent_user")


class TestSessionState:
    """SessionState 枚举测试"""

    def test_values(self):
        """检查所有值"""
        assert SessionState.IDLE.value == "idle"
        assert SessionState.ACQUIRING.value == "acquiring"
        assert SessionState.ACTIVE.value == "active"
