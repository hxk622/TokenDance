"""
SandboxManager 单元测试

测试风险评估、路由选择、确认流程。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.sandbox.confirmation import AutoApproveConfirmationService
from app.sandbox.exceptions import ExecutionRejectedError
from app.sandbox.manager import SandboxManager
from app.sandbox.risk_policy import RiskLevel
from app.sandbox.types import ExecutionRequest, ExecutionResult, SandboxType, SecurityMode


class TestSandboxManager:
    """SandboxManager 测试"""

    @pytest.fixture
    def manager(self) -> SandboxManager:
        """创建管理器（自动批准模式）"""
        confirmation_service = AutoApproveConfirmationService()
        return SandboxManager(
            security_mode=SecurityMode.PERMISSIVE,
            confirmation_service=confirmation_service,
        )

    # ==================== 基本执行测试 ====================

    @pytest.mark.asyncio
    async def test_execute_safe_python_code(self, manager: SandboxManager):
        """执行安全的 Python 代码"""
        request = ExecutionRequest(code="print('Hello')", language="python")

        with patch(
            "app.sandbox.executors.subprocess_executor.SubprocessExecutor.execute"
        ) as mock_execute:
            mock_execute.return_value = ExecutionResult(
                success=True,
                stdout="Hello\n",
                exit_code=0,
                sandbox_type=SandboxType.SUBPROCESS,
            )

            result = await manager.execute(request)

            assert result.success
            assert result.stdout == "Hello\n"
            assert result.sandbox_type == SandboxType.SUBPROCESS

    @pytest.mark.asyncio
    async def test_execute_high_risk_python_code(self, manager: SandboxManager):
        """执行高风险 Python 代码"""
        request = ExecutionRequest(code="import os\nos.getcwd()", language="python")

        with patch(
            "app.sandbox.executors.docker_executor.DockerExecutor.execute"
        ) as mock_execute:
            mock_execute.return_value = ExecutionResult(
                success=True,
                stdout="/workspace\n",
                exit_code=0,
                sandbox_type=SandboxType.DOCKER_SIMPLE,
            )

            result = await manager.execute(request)

            assert result.success
            assert result.sandbox_type == SandboxType.DOCKER_SIMPLE

    @pytest.mark.asyncio
    async def test_execute_critical_code_requires_confirmation(
        self, manager: SandboxManager
    ):
        """CRITICAL 代码需要确认"""
        request = ExecutionRequest(code="eval('1+1')", language="python")

        # AutoApprove 会自动批准
        with patch(
            "app.sandbox.executors.docker_executor.DockerExecutor.execute"
        ) as mock_execute:
            mock_execute.return_value = ExecutionResult(
                success=True,
                stdout="2\n",
                exit_code=0,
                sandbox_type=SandboxType.DOCKER_SIMPLE,
            )

            result = await manager.execute(request)

            assert result.success

    # ==================== 路由选择测试 ====================

    @pytest.mark.asyncio
    async def test_route_safe_to_subprocess(self, manager: SandboxManager):
        """SAFE 路由到 subprocess"""
        request = ExecutionRequest(code="print(1)", language="python")

        with patch(
            "app.sandbox.executors.subprocess_executor.SubprocessExecutor.execute"
        ) as mock_execute:
            mock_execute.return_value = ExecutionResult(
                success=True, stdout="1\n", exit_code=0
            )

            result = await manager.execute(request)

            assert result.success
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_high_to_docker(self, manager: SandboxManager):
        """HIGH 路由到 Docker"""
        request = ExecutionRequest(code="import os", language="python")

        with patch(
            "app.sandbox.executors.docker_executor.DockerExecutor.execute"
        ) as mock_execute:
            mock_execute.return_value = ExecutionResult(
                success=True, stdout="", exit_code=0
            )

            result = await manager.execute(request)

            assert result.success
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_explicit_sandbox_type_override(self, manager: SandboxManager):
        """显式指定沙箱类型"""
        request = ExecutionRequest(
            code="print(1)",
            language="python",
            sandbox_type=SandboxType.DOCKER_SIMPLE,  # 显式指定
        )

        with patch(
            "app.sandbox.executors.docker_executor.DockerExecutor.execute"
        ) as mock_execute:
            mock_execute.return_value = ExecutionResult(
                success=True, stdout="1\n", exit_code=0
            )

            result = await manager.execute(request)

            assert result.success
            mock_execute.assert_called_once()  # 使用 Docker 而不是 subprocess

    # ==================== STRICT 模式测试 ====================

    @pytest.mark.asyncio
    async def test_strict_mode_forces_isolation(self):
        """STRICT 模式强制隔离"""
        manager = SandboxManager(
            security_mode=SecurityMode.STRICT,
            confirmation_service=AutoApproveConfirmationService(),
        )

        request = ExecutionRequest(code="import os", language="python")

        with patch(
            "app.sandbox.executors.docker_executor.DockerExecutor.execute"
        ) as mock_execute:
            mock_execute.return_value = ExecutionResult(
                success=True, stdout="", exit_code=0
            )

            result = await manager.execute(request)

            assert result.success
            mock_execute.assert_called_once()

    # ==================== Shell 命令测试 ====================

    @pytest.mark.asyncio
    async def test_execute_safe_shell_command(self, manager: SandboxManager):
        """执行安全的 Shell 命令"""
        request = ExecutionRequest(code="ls -la", language="shell")

        with patch(
            "app.sandbox.executors.subprocess_executor.SubprocessExecutor.execute"
        ) as mock_execute:
            mock_execute.return_value = ExecutionResult(
                success=True, stdout="total 0\n", exit_code=0
            )

            result = await manager.execute(request)

            assert result.success

    @pytest.mark.asyncio
    async def test_execute_dangerous_shell_rejected(self, manager: SandboxManager):
        """危险的 Shell 命令被拒绝"""
        request = ExecutionRequest(code="rm -rf /", language="shell")

        with pytest.raises(ExecutionRejectedError, match="REJECT"):
            await manager.execute(request)

    # ==================== 风险评估测试 ====================

    def test_assess_code_safe(self, manager: SandboxManager):
        """评估安全代码"""
        result = manager.assess_code("print('Hello')", "python")

        assert result.level == RiskLevel.SAFE
        assert not result.requires_confirmation

    def test_assess_code_high(self, manager: SandboxManager):
        """评估高风险代码"""
        result = manager.assess_code("import os", "python")

        assert result.level == RiskLevel.HIGH
        assert result.requires_confirmation

    def test_assess_code_critical(self, manager: SandboxManager):
        """评估关键风险代码"""
        result = manager.assess_code("eval('code')", "python")

        assert result.level == RiskLevel.CRITICAL
        assert result.requires_confirmation

    # ==================== 错误处理测试 ====================

    @pytest.mark.asyncio
    async def test_executor_failure_propagates(self, manager: SandboxManager):
        """执行器失败传播"""
        request = ExecutionRequest(code="print(1)", language="python")

        with patch(
            "app.sandbox.executors.subprocess_executor.SubprocessExecutor.execute"
        ) as mock_execute:
            mock_execute.return_value = ExecutionResult(
                success=False,
                stderr="Error",
                error="执行失败",
                exit_code=1,
            )

            result = await manager.execute(request)

            assert not result.success
            assert result.error == "执行失败"

    # ==================== 降级测试 ====================

    @pytest.mark.asyncio
    async def test_docker_fallback_to_subprocess(self, manager: SandboxManager):
        """Docker 不可用时降级到 subprocess"""
        request = ExecutionRequest(code="import os", language="python")

        with patch(
            "app.sandbox.executors.docker_executor.DockerExecutor.execute"
        ) as mock_docker, patch(
            "app.sandbox.executors.subprocess_executor.SubprocessExecutor.execute"
        ) as mock_subprocess:
            # Docker 失败
            mock_docker.side_effect = Exception("Docker not available")

            # subprocess 成功
            mock_subprocess.return_value = ExecutionResult(
                success=True, stdout="", exit_code=0
            )

            result = await manager.execute(request)

            assert result.success
            mock_subprocess.assert_called_once()
