"""
SandboxManager 单元测试

测试风险评估、路由选择、确认流程。
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.sandbox.confirmation import AutoApproveConfirmationService
from app.sandbox.manager import SandboxManager
from app.sandbox.risk_policy import RiskLevel, SecurityMode
from app.sandbox.types import ExecutionRequest, ExecutionResult, SandboxType
from app.sandbox.workspace import AgentWorkspace, WorkspaceConfig


class TestSandboxManager:
    """SandboxManager 测试"""

    @pytest.fixture
    def workspace(self, tmp_path: Path) -> AgentWorkspace:
        """创建临时工作空间"""
        config = WorkspaceConfig(base_dir=str(tmp_path))
        return AgentWorkspace("test_session", config)

    @pytest.fixture
    def manager(self, workspace: AgentWorkspace) -> SandboxManager:
        """创建管理器（自动批准模式）"""
        confirmation_service = AutoApproveConfirmationService()
        return SandboxManager(
            session_id="test_session",
            workspace=workspace,
            security_mode=SecurityMode.PERMISSIVE,
            confirmation_service=confirmation_service,
        )

    # ==================== 基本执行测试 ====================

    @pytest.mark.asyncio
    async def test_execute_safe_python_code(self, manager: SandboxManager):
        """执行安全的 Python 代码（实际执行）"""
        request = ExecutionRequest(code="print('Hello')")

        result = await manager.execute(request)

        assert result.success
        assert "Hello" in result.stdout
        assert result.sandbox_type == SandboxType.SUBPROCESS

    @pytest.mark.asyncio
    async def test_execute_shell_ls(self, manager: SandboxManager):
        """执行安全的 shell 命令（实际执行）"""
        request = ExecutionRequest(code="echo 'hello'", language="shell")

        result = await manager.execute(request)

        assert result.success
        assert "hello" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_dangerous_shell_rejected(self, manager: SandboxManager):
        """危险的 Shell 命令被拒绝"""
        request = ExecutionRequest(code="rm -rf /", language="shell")

        result = await manager.execute(request)

        assert not result.success
        assert "拒绝" in result.error or "REJECT" in result.error
