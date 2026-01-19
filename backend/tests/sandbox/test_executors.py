"""
Executor 单元测试

注意：这些执行器需要 session_id 和 workspace，测试时使用 mock 或实际创建。
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.sandbox.executors.aio import AIOSandboxClient
from app.sandbox.executors.docker import DockerSimpleSandbox
from app.sandbox.executors.subprocess_executor import SubprocessExecutor
from app.sandbox.types import ExecutionRequest, SandboxType
from app.sandbox.workspace import AgentWorkspace, WorkspaceConfig


class TestSubprocessExecutor:
    """SubprocessExecutor 测试"""

    @pytest.fixture
    def workspace(self, tmp_path: Path) -> AgentWorkspace:
        """创建临时工作空间"""
        config = WorkspaceConfig(base_dir=str(tmp_path))
        return AgentWorkspace("test_session", config)

    @pytest.fixture
    def executor(self, workspace: AgentWorkspace) -> SubprocessExecutor:
        return SubprocessExecutor("test_session", workspace)

    @pytest.mark.asyncio
    async def test_execute_python_success(self, executor: SubprocessExecutor):
        """执行成功的 Python 代码（实际执行）"""
        request = ExecutionRequest(code="print('Hello')")

        result = await executor.execute(request)

        assert result.success
        assert "Hello" in result.stdout
        assert result.exit_code == 0
        assert result.sandbox_type == SandboxType.SUBPROCESS

    @pytest.mark.asyncio
    async def test_execute_python_with_error(self, executor: SubprocessExecutor):
        """执行有错误的 Python 代码"""
        request = ExecutionRequest(code="1/0")

        result = await executor.execute(request)

        assert not result.success
        assert "ZeroDivisionError" in result.stderr
        assert result.exit_code != 0

    @pytest.mark.asyncio
    async def test_execute_shell_command(self, executor: SubprocessExecutor):
        """执行 Shell 命令"""
        request = ExecutionRequest(code="echo 'test'", language="shell")

        result = await executor.execute(request)

        assert result.success
        assert "test" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_unsupported_language(self, executor: SubprocessExecutor):
        """不支持的语言"""
        request = ExecutionRequest(code="code", language="rust")

        result = await executor.execute(request)

        assert not result.success
        assert "不支持" in result.error


class TestDockerSimpleSandbox:
    """DockerSimpleSandbox 测试"""

    @pytest.fixture
    def workspace(self, tmp_path: Path) -> AgentWorkspace:
        """创建临时工作空间"""
        config = WorkspaceConfig(base_dir=str(tmp_path))
        return AgentWorkspace("test_session", config)

    @pytest.fixture
    def executor(self, workspace: AgentWorkspace) -> DockerSimpleSandbox:
        return DockerSimpleSandbox("test_session", workspace)

    @pytest.mark.asyncio
    async def test_execute_python_in_container(self, executor: DockerSimpleSandbox):
        """在容器中执行 Python 代码（模拟）"""
        request = ExecutionRequest(code="print('Docker')")

        with patch.object(executor, "_get_docker_client") as mock_get_client:
            mock_client = MagicMock()
            mock_container = MagicMock()

            # 设置 containers.create 返回模拟容器
            mock_client.containers.create.return_value = mock_container
            mock_container.start = MagicMock()
            mock_container.wait.return_value = {"StatusCode": 0}
            mock_container.logs.side_effect = [b"Docker\n", b""]  # stdout, stderr
            mock_container.remove = MagicMock()

            mock_get_client.return_value = mock_client

            result = await executor.execute(request)

            assert result.success
            assert "Docker" in result.stdout
            assert result.sandbox_type == SandboxType.DOCKER_SIMPLE

    @pytest.mark.asyncio
    async def test_unsupported_language(self, executor: DockerSimpleSandbox):
        """不支持的语言"""
        request = ExecutionRequest(code="code", language="rust")

        with patch.object(executor, "_get_docker_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            result = await executor.execute(request)

            assert not result.success
            assert "不支持" in result.error


class TestAIOSandboxClient:
    """AIOSandboxClient 测试"""

    @pytest.fixture
    def workspace(self, tmp_path: Path) -> AgentWorkspace:
        """创建临时工作空间"""
        config = WorkspaceConfig(base_dir=str(tmp_path))
        return AgentWorkspace("test_session", config)

    @pytest.fixture
    def client(self, workspace: AgentWorkspace) -> AIOSandboxClient:
        return AIOSandboxClient(
            session_id="test_session",
            workspace=workspace,
            base_url="http://localhost:8080",
        )

    @pytest.mark.asyncio
    async def test_execute_not_connected(self, client: AIOSandboxClient):
        """未连接时执行"""
        request = ExecutionRequest(code="print('AIO')")

        result = await client.execute(request)

        assert not result.success
        assert "未连接" in result.error

    @pytest.mark.asyncio
    async def test_connect_and_execute(self, client: AIOSandboxClient):
        """连接并执行（模拟）"""
        request = ExecutionRequest(code="print('AIO')")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_http_client = AsyncMock()
            mock_client_class.return_value = mock_http_client

            # 模拟连接响应
            connect_response = AsyncMock()
            connect_response.json.return_value = {"sandbox_id": "sandbox_123"}
            connect_response.raise_for_status = MagicMock()
            mock_http_client.post.return_value = connect_response

            await client.connect()

            assert client._sandbox_id == "sandbox_123"

            # 模拟执行响应
            exec_response = AsyncMock()
            exec_response.json.return_value = {
                "success": True,
                "stdout": "AIO\n",
                "stderr": "",
                "exit_code": 0,
            }
            exec_response.raise_for_status = MagicMock()
            mock_http_client.post.return_value = exec_response

            result = await client.execute(request)

            assert result.success
            assert "AIO" in result.stdout
            assert result.sandbox_type == SandboxType.AIO_SANDBOX

    @pytest.mark.asyncio
    async def test_disconnect(self, client: AIOSandboxClient):
        """断开连接"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_http_client = AsyncMock()
            mock_client_class.return_value = mock_http_client

            # 模拟连接
            connect_response = AsyncMock()
            connect_response.json.return_value = {"sandbox_id": "sandbox_123"}
            connect_response.raise_for_status = MagicMock()
            mock_http_client.post.return_value = connect_response

            await client.connect()
            assert client._sandbox_id == "sandbox_123"

            # 断开连接
            await client.disconnect()
            assert client._sandbox_id is None
            assert client._client is None
