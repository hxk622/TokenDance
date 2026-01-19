"""
AIO Sandbox 容器池

解决问题：容器生命周期管理、启动延迟、资源浪费

策略：
- 维护 N 个热实例，按需分配
- Session 绑定：同一 Session 复用同一实例
- 空闲回收：超时销毁
- 使用次数限制：防止内存泄漏
"""

import asyncio
import logging
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Any

from app.sandbox.exceptions import ConcurrentAccessError

if TYPE_CHECKING:
    from app.sandbox.executors.aio import AIOSandboxClient

logger = logging.getLogger(__name__)


class SessionState(str, Enum):
    """Session 状态

    用于防止 TOCTOU（Time Of Check To Time Of Use）问题。
    """

    IDLE = "idle"  # 空闲，可分配
    ACQUIRING = "acquiring"  # 正在获取中，防止重复创建
    BUSY = "busy"  # 正在使用中


@dataclass
class PooledSandbox:
    """池化的 Sandbox 实例"""

    sandbox: Any  # AIOSandboxClient, 使用 Any 避免循环导入
    session_id: str
    state: SessionState = SessionState.IDLE
    created_at: datetime = field(default_factory=datetime.now)
    last_used_at: datetime = field(default_factory=datetime.now)
    use_count: int = 0


@dataclass
class PoolConfig:
    """池配置"""

    max_instances: int = 10  # 最大实例数
    min_instances: int = 2  # 最小预热数
    idle_timeout_seconds: int = 300  # 5分钟空闲超时
    max_use_count: int = 100  # 单实例最大使用次数
    cleanup_interval: int = 60  # 清理检查间隔


class AIOSandboxPool:
    """AIO Sandbox 容器池

    修复 TOCTOU 问题：
    1. 引入 SessionState.ACQUIRING 状态
    2. 在锁内标记状态，锁外创建
    3. 创建失败时清理占位符
    """

    def __init__(
        self,
        config: PoolConfig | None = None,
        base_url: str = "http://localhost:8080",
    ):
        self.config = config or PoolConfig()
        self.base_url = base_url

        self._session_map: dict[str, PooledSandbox] = {}
        self._idle_queue: OrderedDict[str, PooledSandbox] = OrderedDict()
        self._semaphore = asyncio.Semaphore(self.config.max_instances)
        self._lock = asyncio.Lock()
        self._cleanup_task: asyncio.Task[None] | None = None
        self._running = False

    async def start(self) -> None:
        """启动池"""
        self._running = True
        await self._warmup()
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(f"AIOSandboxPool started, min={self.config.min_instances}")

    async def stop(self) -> None:
        """停止池"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        async with self._lock:
            for pooled in list(self._session_map.values()):
                await self._destroy(pooled)
            self._session_map.clear()
            self._idle_queue.clear()

    async def _warmup(self) -> None:
        """预热实例"""
        for i in range(self.config.min_instances):
            try:
                warmup_id = f"warmup_{i}"
                pooled = await self._create_pooled(warmup_id)
                async with self._lock:
                    self._idle_queue[warmup_id] = pooled
            except Exception as e:
                logger.error(f"Warmup {i} failed: {e}")

    async def acquire(self, session_id: str) -> "AIOSandboxClient":
        """获取实例

        修复 TOCTOU 问题：
        1. 在锁内检查并标记 ACQUIRING
        2. 在锁外创建（耗时操作）
        3. 创建失败时清理占位符

        Args:
            session_id: 会话 ID

        Returns:
            AIOSandboxClient: 沙箱客户端

        Raises:
            ConcurrentAccessError: 如果同一 session 已在使用
        """
        async with self._lock:
            # 已有绑定
            if session_id in self._session_map:
                pooled = self._session_map[session_id]

                if pooled.state == SessionState.BUSY:
                    raise ConcurrentAccessError(f"Session {session_id} 正在被使用")
                if pooled.state == SessionState.ACQUIRING:
                    raise ConcurrentAccessError(f"Session {session_id} 正在初始化")

                pooled.state = SessionState.BUSY
                pooled.last_used_at = datetime.now()
                pooled.use_count += 1
                return pooled.sandbox

            # 从空闲队列获取
            if self._idle_queue:
                old_id, pooled = self._idle_queue.popitem(last=False)

                # 检查是否需要重建（使用次数过多）
                if pooled.use_count >= self.config.max_use_count:
                    await self._destroy(pooled)
                    # 继续创建新实例
                else:
                    # 复用空闲实例
                    pooled.session_id = session_id
                    pooled.state = SessionState.BUSY
                    pooled.last_used_at = datetime.now()
                    pooled.use_count += 1
                    self._session_map[session_id] = pooled
                    return pooled.sandbox

            # 创建新实例：先标记为 ACQUIRING，防止其他协程重复创建
            placeholder = PooledSandbox(
                sandbox=None,  # type: ignore
                session_id=session_id,
                state=SessionState.ACQUIRING,
            )
            self._session_map[session_id] = placeholder

        # 锁外创建（耗时操作）
        try:
            await self._semaphore.acquire()
            pooled = await self._create_pooled(session_id)

            async with self._lock:
                # 更新占位符
                self._session_map[session_id] = pooled
                pooled.state = SessionState.BUSY
                pooled.last_used_at = datetime.now()
                pooled.use_count = 1

            return pooled.sandbox

        except Exception as e:
            # 创建失败，清理占位符
            async with self._lock:
                self._session_map.pop(session_id, None)
            self._semaphore.release()
            raise RuntimeError(f"创建 Sandbox 失败: {e}") from e

    async def release(self, session_id: str) -> None:
        """释放实例"""
        async with self._lock:
            if session_id in self._session_map:
                pooled = self._session_map[session_id]
                pooled.state = SessionState.IDLE
                pooled.last_used_at = datetime.now()

    async def _create_pooled(self, session_id: str) -> PooledSandbox:
        """创建池化实例"""
        # 延迟导入避免循环依赖
        from app.sandbox.executors.aio import AIOSandboxClient
        from app.sandbox.workspace import AgentWorkspace

        workspace = AgentWorkspace(session_id)
        sandbox = AIOSandboxClient(session_id, workspace, base_url=self.base_url)
        await sandbox.connect()

        return PooledSandbox(sandbox=sandbox, session_id=session_id)

    async def _destroy(self, pooled: PooledSandbox) -> None:
        """销毁实例"""
        try:
            if pooled.sandbox:
                await pooled.sandbox.disconnect()
        except Exception as e:
            logger.error(f"Destroy failed: {e}")
        finally:
            self._semaphore.release()

    async def _cleanup_loop(self) -> None:
        """清理循环"""
        while self._running:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                await self._cleanup_idle()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    async def _cleanup_idle(self) -> None:
        """清理空闲实例"""
        cutoff = datetime.now() - timedelta(seconds=self.config.idle_timeout_seconds)
        to_destroy: list[PooledSandbox] = []

        async with self._lock:
            for sid, pooled in list(self._session_map.items()):
                if pooled.state == SessionState.IDLE and pooled.last_used_at < cutoff:
                    to_destroy.append(pooled)
                    del self._session_map[sid]

            # 保持最小实例
            current = len(self._session_map) + len(self._idle_queue)
            keep = max(0, self.config.min_instances - current)
            to_destroy = to_destroy[keep:]

        for pooled in to_destroy:
            await self._destroy(pooled)
            logger.info(f"Destroyed idle: {pooled.session_id}")

    def get_stats(self) -> dict[str, int]:
        """获取统计"""
        busy = sum(1 for p in self._session_map.values() if p.state == SessionState.BUSY)
        return {
            "total": len(self._session_map),
            "busy": busy,
            "idle": len(self._session_map) - busy,
            "idle_queue": len(self._idle_queue),
            "max": self.config.max_instances,
        }
