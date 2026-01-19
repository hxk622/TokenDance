"""
ConfirmationService 单元测试
"""

import pytest

from app.sandbox.confirmation import (
    AutoApproveConfirmationService,
    AutoRejectConfirmationService,
    CallbackConfirmationService,
    ConfirmationRequest,
    ConfirmationResult,
)
from app.sandbox.risk_policy import RiskLevel


class TestAutoApproveConfirmationService:
    """AutoApproveConfirmationService 测试"""

    @pytest.fixture
    def service(self) -> AutoApproveConfirmationService:
        return AutoApproveConfirmationService()

    @pytest.mark.asyncio
    async def test_auto_approve(self, service: AutoApproveConfirmationService):
        """自动批准所有请求"""
        request = ConfirmationRequest(
            session_id="test",
            action_description="执行危险代码",
            risk_level=RiskLevel.CRITICAL,
            detected_patterns=["eval", "exec"],
            code_preview="eval('危险代码')",
        )

        result = await service.request_confirmation(request)

        assert result.approved
        assert "自动批准" in result.reason or result.reason is None or "开发模式" in str(result.reason)


class TestAutoRejectConfirmationService:
    """AutoRejectConfirmationService 测试"""

    @pytest.fixture
    def service(self) -> AutoRejectConfirmationService:
        return AutoRejectConfirmationService()

    @pytest.mark.asyncio
    async def test_auto_reject(self, service: AutoRejectConfirmationService):
        """自动拒绝所有请求"""
        request = ConfirmationRequest(
            session_id="test",
            action_description="执行代码",
            risk_level=RiskLevel.HIGH,
        )

        result = await service.request_confirmation(request)

        assert not result.approved
        assert "拒绝" in result.reason or "安全" in result.reason


class TestCallbackConfirmationService:
    """CallbackConfirmationService 测试"""

    @pytest.mark.asyncio
    async def test_callback_approve(self):
        """回调批准"""

        async def approve_callback(request: ConfirmationRequest) -> ConfirmationResult:
            return ConfirmationResult(approved=True, reason="回调批准")

        service = CallbackConfirmationService(approve_callback)
        request = ConfirmationRequest(session_id="test")

        result = await service.request_confirmation(request)

        assert result.approved
        assert result.reason == "回调批准"

    @pytest.mark.asyncio
    async def test_callback_reject(self):
        """回调拒绝"""

        async def reject_callback(request: ConfirmationRequest) -> ConfirmationResult:
            return ConfirmationResult(approved=False, reason="回调拒绝")

        service = CallbackConfirmationService(reject_callback)
        request = ConfirmationRequest(session_id="test")

        result = await service.request_confirmation(request)

        assert not result.approved
        assert result.reason == "回调拒绝"

    @pytest.mark.asyncio
    async def test_callback_with_modified_code(self):
        """回调返回修改后的代码"""

        async def modify_callback(request: ConfirmationRequest) -> ConfirmationResult:
            return ConfirmationResult(
                approved=True,
                modified_code="print('安全代码')",
            )

        service = CallbackConfirmationService(modify_callback)
        request = ConfirmationRequest(
            session_id="test",
            code_preview="eval('危险')",
        )

        result = await service.request_confirmation(request)

        assert result.approved
        assert result.modified_code == "print('安全代码')"


class TestConfirmationRequest:
    """ConfirmationRequest 测试"""

    def test_default_values(self):
        """默认值"""
        request = ConfirmationRequest()

        assert request.session_id == ""
        assert request.risk_level == RiskLevel.MEDIUM
        assert request.timeout_seconds == 60
        assert request.detected_patterns == []

    def test_custom_values(self):
        """自定义值"""
        request = ConfirmationRequest(
            session_id="session_123",
            action_description="执行代码",
            risk_level=RiskLevel.CRITICAL,
            detected_patterns=["eval"],
            code_preview="eval('1+1')",
            timeout_seconds=30,
        )

        assert request.session_id == "session_123"
        assert request.risk_level == RiskLevel.CRITICAL
        assert request.timeout_seconds == 30
        assert "eval" in request.detected_patterns

    def test_auto_generated_request_id(self):
        """自动生成 request_id"""
        request1 = ConfirmationRequest()
        request2 = ConfirmationRequest()

        assert request1.request_id != request2.request_id
        assert len(request1.request_id) > 0
