"""
Docker Simple Sandbox 执行器

使用 Docker 容器隔离执行代码。
适用于中高风险代码。
"""

import asyncio
import logging
import time
from typing import Any

from app.sandbox.exceptions import SandboxNotAvailableError, SandboxTimeoutError
from app.sandbox.executors.base import BaseSandboxExecutor
from app.sandbox.types import ExecutionRequest, ExecutionResult, SandboxType
from app.sandbox.workspace import AgentWorkspace

logger = logging.getLogger(__name__)


class DockerSimpleSandbox(BaseSandboxExecutor):
    """Docker Simple Sandbox 执行器

    使用 Docker 容器提供隔离环境。

    特点：
    - 每次执行创建新容器
    - 执行完成后销毁容器
    - 支持 Volume 挂载工作空间
    """

    # 默认镜像
    DEFAULT_IMAGES = {
        "python": "python:3.11-slim",
        "javascript": "node:20-slim",
        "shell": "alpine:latest",
    }

    def __init__(
        self,
        session_id: str,
        workspace: AgentWorkspace,
        images: dict[str, str] | None = None,
    ):
        super().__init__(session_id, workspace)
        self.images = images or self.DEFAULT_IMAGES
        self._docker_client: Any | None = None

    async def _get_docker_client(self) -> Any:
        """获取 Docker 客户端"""
        if self._docker_client is None:
            try:
                import docker

                self._docker_client = docker.from_env()
                # 测试连接
                self._docker_client.ping()
            except ImportError as e:
                raise SandboxNotAvailableError(
                    "Docker SDK 未安装: pip install docker"
                ) from e
            except Exception as e:
                raise SandboxNotAvailableError(f"Docker 不可用: {e}") from e
        return self._docker_client

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """执行代码"""
        start_time = time.time()

        try:
            client = await self._get_docker_client()

            image = self.images.get(request.language)
            if not image:
                return ExecutionResult(
                    success=False,
                    error=f"不支持的语言: {request.language}",
                    sandbox_type=SandboxType.DOCKER_SIMPLE,
                )

            # 构建执行命令
            cmd = self._build_command(request)

            # 运行容器
            result = await self._run_container(client, image, cmd, request)

            result.execution_time_ms = (time.time() - start_time) * 1000
            result.sandbox_type = SandboxType.DOCKER_SIMPLE
            return result

        except SandboxTimeoutError:
            return ExecutionResult(
                success=False,
                error=f"执行超时 ({request.timeout}s)",
                sandbox_type=SandboxType.DOCKER_SIMPLE,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        except SandboxNotAvailableError:
            raise
        except Exception as e:
            logger.error(f"Docker 执行失败: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                sandbox_type=SandboxType.DOCKER_SIMPLE,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    def _build_command(self, request: ExecutionRequest) -> list[str]:
        """构建执行命令"""
        if request.language == "python":
            return ["python", "-c", request.code]
        elif request.language == "javascript":
            return ["node", "-e", request.code]
        elif request.language == "shell":
            return ["sh", "-c", request.code]
        else:
            raise ValueError(f"不支持的语言: {request.language}")

    async def _run_container(
        self,
        client: Any,
        image: str,
        cmd: list[str],
        request: ExecutionRequest,
    ) -> ExecutionResult:
        """运行容器"""
        container = None

        try:
            # 在线程池中运行 Docker 操作（Docker SDK 不是异步的）
            loop = asyncio.get_running_loop()

            # 创建容器
            container = await loop.run_in_executor(
                None,
                lambda: client.containers.create(
                    image=image,
                    command=cmd,
                    volumes=self.workspace.get_volume_mount(),
                    working_dir=self.workspace.container_path,
                    mem_limit=f"{request.max_memory_mb}m",
                    network_mode="none",  # 禁用网络
                    detach=True,
                ),
            )

            # 启动容器
            await loop.run_in_executor(None, container.start)

            # 等待执行完成
            try:
                exit_code = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: container.wait(timeout=request.timeout)),
                    timeout=request.timeout + 5,  # 额外 5 秒用于 Docker 操作
                )
            except TimeoutError:
                # 超时，强制停止
                await loop.run_in_executor(None, lambda: container.stop(timeout=1))
                raise SandboxTimeoutError(f"执行超时 ({request.timeout}s)") from None

            # 分离 stdout 和 stderr
            stdout_logs = await loop.run_in_executor(
                None, lambda: container.logs(stdout=True, stderr=False)
            )
            stderr_logs = await loop.run_in_executor(
                None, lambda: container.logs(stdout=False, stderr=True)
            )

            return ExecutionResult(
                success=exit_code.get("StatusCode", 1) == 0,
                stdout=self._truncate_output(
                    stdout_logs.decode("utf-8", errors="replace"), request
                ),
                stderr=self._truncate_output(
                    stderr_logs.decode("utf-8", errors="replace"), request
                ),
                exit_code=exit_code.get("StatusCode", 1),
            )

        finally:
            # 清理容器
            if container:
                try:
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, lambda: container.remove(force=True))
                except Exception as e:
                    logger.warning(f"清理容器失败: {e}")

    def _truncate_output(self, output: str, request: ExecutionRequest) -> str:
        """截断输出"""
        max_bytes = request.max_output_bytes
        if len(output.encode("utf-8")) > max_bytes:
            truncated = output[: max_bytes // 2]
            return truncated + "\n\n... (输出过长，已截断)"
        return output

    async def cleanup(self) -> None:
        """清理资源"""
        if self._docker_client:
            try:
                self._docker_client.close()
            except Exception:
                pass
            self._docker_client = None
