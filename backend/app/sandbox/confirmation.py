"""
确认服务 - Human-in-the-Loop

解决问题：requires_confirmation=True 但没有实际等待逻辑

提供多种确认服务实现：
- WebSocketConfirmationService: 通过 WebSocket 请求用户确认
- AutoApproveConfirmationService: 自动批准（仅用于测试/开发）
- AutoRejectConfirmationService: 自动拒绝（安全模式）
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.sandbox.exceptions import ConfirmationRejectedError, ConfirmationTimeoutError
from app.sandbox.risk_policy import RiskLevel

logger = logging.getLogger(__name__)


@dataclass
class ConfirmationRequest:
    """确认请求"""

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    action_description: str = ""
    risk_level: RiskLevel = RiskLevel.MEDIUM
    detected_patterns: list[str] = field(default_factory=list)
    code_preview: str = ""
    timeout_seconds: int = 60


@dataclass
class ConfirmationResult:
    """确认结果"""

    approved: bool
    reason: str | None = None
    modified_code: str | None = None  # 用户可能修改代码


class ConfirmationService(ABC):
    """确认服务抽象基类"""

    @abstractmethod
    async def request_confirmation(self, request: ConfirmationRequest) -> ConfirmationResult:
        """请求用户确认

        Args:
            request: 确认请求

        Returns:
            ConfirmationResult: 确认结果
        """
        pass


class WebSocketConfirmationService(ConfirmationService):
    """通过 WebSocket 请求确认

    工作流程：
    1. 发送确认请求到前端
    2. 等待用户响应
    3. 返回确认结果

    前端需要监听 confirmation_required 消息并调用 handle_response。
    """

    def __init__(self, ws_manager: Any):
        """
        Args:
            ws_manager: WebSocket 管理器，需要实现 send_to_session 方法
        """
        self._ws = ws_manager
        self._pending: dict[str, asyncio.Future[ConfirmationResult]] = {}

    async def request_confirmation(self, request: ConfirmationRequest) -> ConfirmationResult:
        """请求用户确认"""
        # 发送确认请求到前端
        await self._ws.send_to_session(
            session_id=request.session_id,
            message={
                "type": "confirmation_required",
                "data": {
                    "request_id": request.request_id,
                    "description": request.action_description,
                    "risk_level": request.risk_level.value,
                    "patterns": request.detected_patterns,
                    "code_preview": request.code_preview[:500],  # 限制预览长度
                },
            },
        )

        # 创建 Future 等待响应
        loop = asyncio.get_running_loop()
        future: asyncio.Future[ConfirmationResult] = loop.create_future()
        self._pending[request.request_id] = future

        try:
            result = await asyncio.wait_for(future, timeout=request.timeout_seconds)
            return result
        except asyncio.TimeoutError:
            logger.warning(f"确认超时: {request.request_id}")
            raise ConfirmationTimeoutError(f"确认超时 ({request.timeout_seconds}s)")
        finally:
            self._pending.pop(request.request_id, None)

    def handle_response(self, request_id: str, response: dict[str, Any]) -> bool:
        """处理前端响应

        前端应该在用户确认后调用此方法。

        Args:
            request_id: 请求 ID
            response: 响应数据，包含 approved, reason, modified_code

        Returns:
            bool: 是否成功处理
        """
        if request_id not in self._pending:
            logger.warning(f"未找到待处理的确认请求: {request_id}")
            return False

        result = ConfirmationResult(
            approved=response.get("approved", False),
            reason=response.get("reason"),
            modified_code=response.get("modified_code"),
        )

        future = self._pending[request_id]
        if not future.done():
            future.set_result(result)
            return True
        return False

    def cancel_pending(self, request_id: str) -> bool:
        """取消待处理的确认请求"""
        if request_id in self._pending:
            future = self._pending.pop(request_id)
            if not future.done():
                future.set_exception(ConfirmationRejectedError("确认被取消"))
                return True
        return False


class AutoApproveConfirmationService(ConfirmationService):
    """自动批准确认服务

    ⚠️ 仅用于测试和开发环境！

    所有确认请求都会被自动批准，并记录警告日志。
    """

    async def request_confirmation(self, request: ConfirmationRequest) -> ConfirmationResult:
        """自动批准"""
        logger.warning(
            f"[AutoApprove] 自动批准高风险操作: "
            f"level={request.risk_level.value}, "
            f"patterns={request.detected_patterns}"
        )
        return ConfirmationResult(approved=True, reason="自动批准（开发模式）")


class AutoRejectConfirmationService(ConfirmationService):
    """自动拒绝确认服务

    用于安全模式，所有需要确认的操作都被拒绝。
    """

    async def request_confirmation(self, request: ConfirmationRequest) -> ConfirmationResult:
        """自动拒绝"""
        logger.info(
            f"[AutoReject] 自动拒绝高风险操作: "
            f"level={request.risk_level.value}, "
            f"patterns={request.detected_patterns}"
        )
        return ConfirmationResult(approved=False, reason="安全模式：自动拒绝高风险操作")


class CallbackConfirmationService(ConfirmationService):
    """回调确认服务

    通过回调函数请求确认，适用于自定义集成场景。
    """

    def __init__(
        self,
        callback: Any,  # Callable[[ConfirmationRequest], Awaitable[ConfirmationResult]]
    ):
        """
        Args:
            callback: 异步回调函数，接收 ConfirmationRequest 返回 ConfirmationResult
        """
        self._callback = callback

    async def request_confirmation(self, request: ConfirmationRequest) -> ConfirmationResult:
        """通过回调请求确认"""
        return await self._callback(request)
