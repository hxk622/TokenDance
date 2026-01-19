"""
Sandbox 管理器 - 统一代码执行入口

解决问题：
1. 工具系统与 Sandbox 割裂 → 统一入口
2. 风险评估不统一 → UnifiedRiskPolicy
3. 确认机制缺失 → ConfirmationService 集成

所有代码执行都应通过 SandboxManager，确保：
- 风险评估
- 确认机制（可选）
- Sandbox 选择
- 资源管理
"""

import dataclasses
import logging
from typing import TYPE_CHECKING

from app.sandbox.confirmation import (
    ConfirmationRequest,
    ConfirmationService,
)
from app.sandbox.exceptions import (
    ConfirmationRejectedError,
    ExecutionRejectedError,
    SandboxNotAvailableError,
)
from app.sandbox.risk_policy import RiskLevel, SecurityMode, UnifiedRiskPolicy
from app.sandbox.types import ExecutionRequest, ExecutionResult, SandboxType
from app.sandbox.workspace import AgentWorkspace

if TYPE_CHECKING:
    from app.sandbox.pool import AIOSandboxPool

logger = logging.getLogger(__name__)


class SandboxManager:
    """Sandbox 管理器 - 统一代码执行入口

    职责：
    1. 接收执行请求
    2. 风险评估（使用 UnifiedRiskPolicy）
    3. 请求确认（如果需要）
    4. 智能路由到合适的 Sandbox
    5. 执行并返回结果

    使用示例：
        manager = SandboxManager(session_id="xxx")
        result = await manager.execute(ExecutionRequest(code="print(1)", language="python"))
    """

    def __init__(
        self,
        session_id: str,
        workspace: AgentWorkspace | None = None,
        aio_pool: "AIOSandboxPool | None" = None,
        confirmation_service: ConfirmationService | None = None,
        security_mode: SecurityMode = SecurityMode.STRICT,
    ):
        """
        Args:
            session_id: 会话 ID
            workspace: 工作空间（可选，自动创建）
            aio_pool: AIO Sandbox 池（可选）
            confirmation_service: 确认服务（可选）
            security_mode: 安全模式
        """
        self.session_id = session_id
        self.workspace = workspace or AgentWorkspace(session_id)
        self.aio_pool = aio_pool
        self.confirmation_service = confirmation_service
        self.security_mode = security_mode

        # 懒加载执行器
        self._subprocess = None
        self._docker_simple = None
        self._aio_sandbox = None

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """执行代码 - 统一入口

        Args:
            request: 执行请求

        Returns:
            ExecutionResult: 执行结果
        """
        # 1. 风险评估
        content_type = "shell" if request.language == "shell" else request.language
        risk = UnifiedRiskPolicy.assess(request.code, content_type)

        logger.info(
            f"风险评估: level={risk.level.value}, "
            f"suggested={risk.suggested_sandbox}, "
            f"patterns={risk.detected_patterns}"
        )

        # 2. 检查是否拒绝
        if risk.suggested_sandbox == "REJECT":
            return ExecutionResult(
                success=False,
                error=f"执行被拒绝: {risk.reason}",
                stderr=f"检测到: {risk.detected_patterns}",
                exit_code=-1,
            )

        # 3. 请求确认（如果需要）
        if risk.requires_confirmation and self.confirmation_service:
            try:
                request = await self._request_confirmation(request, risk)
            except (ConfirmationRejectedError, ExecutionRejectedError) as e:
                return ExecutionResult(
                    success=False,
                    error=str(e),
                    exit_code=-1,
                )

        # 4. 确定 Sandbox 类型
        sandbox_type = request.sandbox_type or UnifiedRiskPolicy.get_required_sandbox(
            risk, self.security_mode
        )
        logger.info(f"选择 Sandbox: {sandbox_type.value}")

        # 5. 路由执行
        if sandbox_type == SandboxType.SUBPROCESS:
            return await self._execute_subprocess(request)
        elif sandbox_type == SandboxType.DOCKER_SIMPLE:
            return await self._execute_docker_simple(request)
        elif sandbox_type == SandboxType.AIO_SANDBOX:
            return await self._execute_aio_sandbox(request)
        else:
            return ExecutionResult(
                success=False,
                error=f"未知 Sandbox 类型: {sandbox_type}",
                exit_code=-1,
            )

    async def _request_confirmation(
        self, request: ExecutionRequest, risk: "RiskLevel"
    ) -> ExecutionRequest:
        """请求用户确认

        Returns:
            ExecutionRequest: 可能被用户修改的请求
        """
        confirm_req = ConfirmationRequest(
            session_id=request.session_id or self.session_id,
            action_description=f"执行 {request.language} 代码",
            risk_level=risk.level,
            detected_patterns=risk.detected_patterns,
            code_preview=request.code,
        )

        result = await self.confirmation_service.request_confirmation(confirm_req)

        if not result.approved:
            raise ConfirmationRejectedError(f"用户拒绝执行: {result.reason}")

        # 用户可能修改了代码
        if result.modified_code:
            logger.info("用户修改了代码")
            return dataclasses.replace(request, code=result.modified_code)

        return request

    async def _execute_subprocess(self, request: ExecutionRequest) -> ExecutionResult:
        """Subprocess 执行"""
        if not self._subprocess:
            from app.sandbox.executors.subprocess_executor import SubprocessExecutor

            self._subprocess = SubprocessExecutor(self.session_id, self.workspace)
        return await self._subprocess.execute(request)

    async def _execute_docker_simple(self, request: ExecutionRequest) -> ExecutionResult:
        """DockerSimple 执行"""
        if not self._docker_simple:
            try:
                from app.sandbox.executors.docker import DockerSimpleSandbox

                self._docker_simple = DockerSimpleSandbox(self.session_id, self.workspace)
            except SandboxNotAvailableError:
                logger.warning("Docker 不可用，回退到 Subprocess")
                return await self._execute_subprocess(request)
        return await self._docker_simple.execute(request)

    async def _execute_aio_sandbox(self, request: ExecutionRequest) -> ExecutionResult:
        """AIO Sandbox 执行"""
        if self.aio_pool:
            # 使用池化实例
            sandbox = await self.aio_pool.acquire(self.session_id)
            try:
                return await sandbox.execute(request)
            finally:
                await self.aio_pool.release(self.session_id)
        else:
            # 非池化模式
            if not self._aio_sandbox:
                try:
                    from app.sandbox.executors.aio import AIOSandboxClient

                    self._aio_sandbox = AIOSandboxClient(self.session_id, self.workspace)
                    await self._aio_sandbox.connect()
                except SandboxNotAvailableError:
                    logger.warning("AIO Sandbox 不可用，回退到 Docker")
                    return await self._execute_docker_simple(request)
            return await self._aio_sandbox.execute(request)

    async def cleanup(self) -> None:
        """清理资源"""
        if self._subprocess:
            await self._subprocess.cleanup()
        if self._docker_simple:
            await self._docker_simple.cleanup()
        if self._aio_sandbox:
            await self._aio_sandbox.cleanup()


# 便捷函数
async def create_sandbox_manager(
    session_id: str,
    security_mode: SecurityMode = SecurityMode.STRICT,
    confirmation_service: ConfirmationService | None = None,
) -> SandboxManager:
    """创建 SandboxManager 的便捷函数

    Args:
        session_id: 会话 ID
        security_mode: 安全模式
        confirmation_service: 确认服务

    Returns:
        SandboxManager: 管理器实例
    """
    return SandboxManager(
        session_id=session_id,
        security_mode=security_mode,
        confirmation_service=confirmation_service,
    )
