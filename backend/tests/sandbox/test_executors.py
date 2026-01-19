"""
Executor 单元测试
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.sandbox.executors.aio import AIOSandboxExecutor
from app.sandbox.executors.docker import DockerExecutor
from app.sandbox.executors.subprocess_executor import SubprocessExecutor
from app.sandbox.types import ExecutionRequest, SandboxType


class TestSubprocessExecutor:
    """SubprocessExecutor 测试"""

    @pytest.fixture
    def executor(self) -> SubprocessExecutor:
        return SubprocessExecutor()

    @pytest.mark.asyncio
    async def test_execute_python_success(self, executor: SubprocessExecutor):
        """执行成功的 Python 代码"""
        request = ExecutionRequest(code="print('Hello')", language="python")

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"Hello\n", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await executor.execute(request)

            assert result.success
            assert result.stdout == "Hello\n"
            assert result.exit_code == 0
            assert result.sandbox_type == SandboxType.SUBPROCESS

    @pytest.mark.asyncio
    async def test_execute_python_with_error(self, executor: SubprocessExecutor):
        """执行有错误的 Python 代码"""
        request = ExecutionRequest(code="1/0", language="python")

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (
                b"",
                b"ZeroDivisionError: division by zero",
            )
            mock_process.returncode = 1
            mock_exec.return_value = mock_process

            result = await executor.execute(request)

            assert not result.success
            assert "ZeroDivisionError" in result.stderr
            assert result.exit_code == 1

    @pytest.mark.asyncio
    async def test_execute_timeout(self, executor: SubprocessExecutor):
        """执行超时"""
        request = ExecutionRequest(
            code="import time; time.sleep(10)", language="python", timeout=1
        )

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.side_effect = asyncio.TimeoutError()
            mock_exec.return_value = mock_process

            result = await executor.execute(request)

            assert not result.success
            assert "超时" in result.error or "timeout" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_shell_command(self, executor: SubprocessExecutor):
        """执行 Shell 命令"""
        request = ExecutionRequest(code="echo 'test'", language="shell")

        with patch("asyncio.create_subprocess_shell") as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"test\n", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await executor.execute(request)

            assert result.success
            assert result.stdout == "test\n"


class TestDockerExecutor:
    """DockerExecutor 测试"""

    @pytest.fixture
    def executor(self) -> DockerExecutor:
        return DockerExecutor()

    @pytest.mark.asyncio
    async def test_execute_python_in_container(self, executor: DockerExecutor):
        """在容器中执行 Python 代码"""
        request = ExecutionRequest(code="print('Docker')", language="python")

        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_container = MagicMock()
            mock_client.containers.run.return_value = mock_container
            mock_container.logs.return_value = b"Docker\n"
            mock_container.wait.return_value = {"StatusCode": 0}
            mock_docker.return_value = mock_client

            result = await executor.execute(request)

            assert result.success
            assert result.stdout == "Docker\n"
            assert result.sandbox_type == SandboxType.DOCKER_SIMPLE

    @pytest.mark.asyncio
    async def test_execute_with_memory_limit(self, executor: DockerExecutor):
        """内存限制"""
        request = ExecutionRequest(
            code="print('test')", language="python", max_memory_mb=128
        )

        with patch("docker.from_env") as mock_docker:
            mock_client = MagicMock()
            mock_container = MagicMock()
            mock_client.containers.run.return_value = mock_container
            mock_container.logs.return_value = b"test\n"
            mock_container.wait.return_value = {"StatusCode": 0}
            mock_docker.return_value = mock_client

            result = await executor.execute(request)

            assert result.success
            # 检查 mem_limit 参数被传递
            call_kwargs = mock_client.containers.run.call_args[1]
            assert "mem_limit" in call_kwargs

    @pytest.mark.asyncio
    async def test_execute_with_workspace(self, executor: DockerExecutor):
        """使用工作空间"""
        request = ExecutionRequest(code="print('test')", language="python")

        with patch("docker.from_env") as mock_docker, patch(
            "app.sandbox.workspace.AgentWorkspace"
        ) as mock_workspace_class:
            mock_client = MagicMock()
            mock_container = MagicMock()
            mock_client.containers.run.return_value = mock_container
            mock_container.logs.return_value = b"test\n"
            mock_container.wait.return_value = {"StatusCode": 0}
            mock_docker.return_value = mock_client

            mock_workspace = MagicMock()
            mock_workspace.get_volume_mount.return_value = {
                "/tmp/workspace": {"bind": "/workspace", "mode": "rw"}
            }
            mock_workspace_class.return_value = mock_workspace

            result = await executor.execute(request, workspace=mock_workspace)

            assert result.success
            # 检查 volumes 参数被传递
            call_kwargs = mock_client.containers.run.call_args[1]
            assert "volumes" in call_kwargs


class TestAIOSandboxExecutor:
    """AIOSandboxExecutor 测试"""

    @pytest.fixture
    def executor(self) -> AIOSandboxExecutor:
        return AIOSandboxExecutor(api_url="http://localhost:8000")

    @pytest.mark.asyncio
    async def test_execute_via_api(self, executor: AIOSandboxExecutor):
        """通过 API 执行代码"""
        request = ExecutionRequest(
            code="print('AIO')", language="python", session_id="session_123"
        )

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={
                    "success": True,
                    "stdout": "AIO\n",
                    "stderr": "",
                    "exit_code": 0,
                }
            )
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await executor.execute(request)

            assert result.success
            assert result.stdout == "AIO\n"
            assert result.sandbox_type == SandboxType.AIO_SANDBOX

    @pytest.mark.asyncio
    async def test_execute_api_failure(self, executor: AIOSandboxExecutor):
        """API 调用失败"""
        request = ExecutionRequest(code="print(1)", language="python")

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Internal Server Error")
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await executor.execute(request)

            assert not result.success
            assert "500" in result.error or "失败" in result.error

    @pytest.mark.asyncio
    async def test_execute_without_session(self, executor: AIOSandboxExecutor):
        """没有 session_id 的执行"""
        request = ExecutionRequest(code="print(1)", language="python")

        result = await executor.execute(request)

        assert not result.success
        assert "session_id" in result.error


# 导入 asyncio 用于超时测试
import asyncio
