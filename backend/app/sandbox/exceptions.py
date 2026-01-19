"""
Sandbox 异常定义

所有 Sandbox 相关的异常类型。
"""


class SandboxError(Exception):
    """Sandbox 基础异常"""

    pass


class PathTraversalError(SandboxError):
    """路径遍历攻击检测

    当检测到试图访问 workspace 外部路径时抛出。
    """

    pass


class ConcurrentAccessError(SandboxError):
    """并发访问错误

    当同一 session 尝试同时获取多个 sandbox 实例时抛出。
    """

    pass


class SandboxTimeoutError(SandboxError):
    """执行超时"""

    pass


class SandboxNotAvailableError(SandboxError):
    """Sandbox 不可用

    当请求的 sandbox 类型不可用时抛出（如 Docker 未安装）。
    """

    pass


class ExecutionRejectedError(SandboxError):
    """执行被拒绝

    当代码被风险策略拒绝执行时抛出。
    """

    pass


class ConfirmationTimeoutError(SandboxError):
    """确认超时

    当等待用户确认超时时抛出。
    """

    pass


class ConfirmationRejectedError(SandboxError):
    """用户拒绝确认

    当用户明确拒绝执行时抛出。
    """

    pass
