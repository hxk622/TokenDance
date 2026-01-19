"""
Sandbox 执行器

提供多种执行后端：
- SubprocessExecutor: 直接子进程，最轻量
- DockerSimpleSandbox: Docker 隔离
- AIOSandboxClient: 完整 AIO 环境
"""

from app.sandbox.executors.base import BaseSandboxExecutor

__all__ = [
    "BaseSandboxExecutor",
]
