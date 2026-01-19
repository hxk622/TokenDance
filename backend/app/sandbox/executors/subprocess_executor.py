"""
Subprocess 执行器

最轻量的执行方式，直接在子进程中运行。
仅用于安全代码（RiskLevel.SAFE）。
"""

import asyncio
import logging
import sys
import tempfile
import time
from pathlib import Path

from app.sandbox.exceptions import SandboxTimeoutError
from app.sandbox.executors.base import BaseSandboxExecutor
from app.sandbox.types import ExecutionRequest, ExecutionResult, SandboxType
from app.sandbox.workspace import AgentWorkspace

logger = logging.getLogger(__name__)


class SubprocessExecutor(BaseSandboxExecutor):
    """Subprocess 执行器

    直接在子进程中执行代码，无容器隔离。

    ⚠️ 安全警告：
    - 仅用于经过风险评估的安全代码
    - 生产环境应使用 SecurityMode.STRICT 强制 Docker 隔离
    """

    def __init__(self, session_id: str, workspace: AgentWorkspace):
        super().__init__(session_id, workspace)

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """执行代码"""
        start_time = time.time()

        try:
            if request.language == "python":
                result = await self._execute_python(request)
            elif request.language == "javascript":
                result = await self._execute_javascript(request)
            elif request.language == "shell":
                result = await self._execute_shell(request)
            else:
                return ExecutionResult(
                    success=False,
                    error=f"不支持的语言: {request.language}",
                    sandbox_type=SandboxType.SUBPROCESS,
                )

            result.execution_time_ms = (time.time() - start_time) * 1000
            result.sandbox_type = SandboxType.SUBPROCESS
            return result

        except SandboxTimeoutError:
            return ExecutionResult(
                success=False,
                error=f"执行超时 ({request.timeout}s)",
                sandbox_type=SandboxType.SUBPROCESS,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            logger.error(f"Subprocess 执行失败: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                sandbox_type=SandboxType.SUBPROCESS,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    async def _execute_python(self, request: ExecutionRequest) -> ExecutionResult:
        """执行 Python 代码"""
        # 写入临时文件
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, dir=str(self.workspace.host_path / "temp")
        ) as f:
            f.write(request.code)
            script_path = f.name

        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace.host_path),
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=request.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise SandboxTimeoutError(f"执行超时 ({request.timeout}s)")

            return ExecutionResult(
                success=process.returncode == 0,
                stdout=self._truncate_output(stdout.decode("utf-8", errors="replace"), request),
                stderr=self._truncate_output(stderr.decode("utf-8", errors="replace"), request),
                exit_code=process.returncode or 0,
            )
        finally:
            # 清理临时文件
            Path(script_path).unlink(missing_ok=True)

    async def _execute_javascript(self, request: ExecutionRequest) -> ExecutionResult:
        """执行 JavaScript 代码"""
        # 写入临时文件
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", delete=False, dir=str(self.workspace.host_path / "temp")
        ) as f:
            f.write(request.code)
            script_path = f.name

        try:
            process = await asyncio.create_subprocess_exec(
                "node",
                script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace.host_path),
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=request.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise SandboxTimeoutError(f"执行超时 ({request.timeout}s)")

            return ExecutionResult(
                success=process.returncode == 0,
                stdout=self._truncate_output(stdout.decode("utf-8", errors="replace"), request),
                stderr=self._truncate_output(stderr.decode("utf-8", errors="replace"), request),
                exit_code=process.returncode or 0,
            )
        finally:
            Path(script_path).unlink(missing_ok=True)

    async def _execute_shell(self, request: ExecutionRequest) -> ExecutionResult:
        """执行 Shell 命令"""
        process = await asyncio.create_subprocess_shell(
            request.code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.workspace.host_path),
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=request.timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise SandboxTimeoutError(f"执行超时 ({request.timeout}s)")

        return ExecutionResult(
            success=process.returncode == 0,
            stdout=self._truncate_output(stdout.decode("utf-8", errors="replace"), request),
            stderr=self._truncate_output(stderr.decode("utf-8", errors="replace"), request),
            exit_code=process.returncode or 0,
        )

    def _truncate_output(self, output: str, request: ExecutionRequest) -> str:
        """截断输出"""
        max_bytes = request.max_output_bytes
        if len(output.encode("utf-8")) > max_bytes:
            # 简单截断
            truncated = output[: max_bytes // 2]
            return truncated + f"\n\n... (输出过长，已截断，原始长度约 {len(output)} 字符)"
        return output
