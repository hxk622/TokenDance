"""
Sandbox 类型定义

核心数据类型和枚举。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SandboxType(str, Enum):
    """Sandbox 类型"""

    SUBPROCESS = "subprocess"  # 最轻量，直接子进程
    DOCKER_SIMPLE = "docker_simple"  # Docker 隔离
    AIO_SANDBOX = "aio_sandbox"  # 完整 AIO 环境


class SecurityMode(str, Enum):
    """安全模式

    控制 Sandbox 选择策略：
    - PERMISSIVE: 允许 subprocess，适合开发环境
    - STRICT: 强制 Docker 隔离，适合生产环境
    """

    PERMISSIVE = "permissive"
    STRICT = "strict"


@dataclass
class ExecutionRequest:
    """执行请求"""

    code: str
    language: str = "python"  # python | javascript | shell
    timeout: int = 30
    sandbox_type: SandboxType | None = None  # None = 自动选择
    session_id: str = ""
    max_memory_mb: int = 512
    max_output_bytes: int = 10 * 1024 * 1024  # 10MB


@dataclass
class ExecutionResult:
    """执行结果"""

    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    error: str | None = None
    sandbox_type: SandboxType = SandboxType.SUBPROCESS
    execution_time_ms: float = 0.0
    files_created: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "error": self.error,
            "sandbox_type": self.sandbox_type.value,
            "execution_time_ms": self.execution_time_ms,
            "files_created": self.files_created,
        }
