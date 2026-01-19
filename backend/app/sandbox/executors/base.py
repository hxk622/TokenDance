"""
Sandbox 执行器基类
"""

from abc import ABC, abstractmethod

from app.sandbox.types import ExecutionRequest, ExecutionResult
from app.sandbox.workspace import AgentWorkspace


class BaseSandboxExecutor(ABC):
    """Sandbox 执行器基类"""

    def __init__(self, session_id: str, workspace: AgentWorkspace):
        self.session_id = session_id
        self.workspace = workspace

    @abstractmethod
    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """执行代码

        Args:
            request: 执行请求

        Returns:
            ExecutionResult: 执行结果
        """
        pass

    async def cleanup(self) -> None:
        """清理资源"""
        pass
