"""
Sandbox 模块 - 安全代码执行环境

提供统一的代码执行入口，支持多种沙箱后端：
- Subprocess: 轻量级，适合安全代码
- DockerSimple: Docker 隔离，适合中高风险代码
- AIOSandbox: 完整环境，支持浏览器和持久化

核心组件：
- SandboxManager: 统一执行入口
- UnifiedRiskPolicy: 风险评估
- AgentWorkspace: 统一文件路径
- AIOSandboxPool: 容器池管理
- BrowserRouter: 浏览器路由
- ConfirmationService: Human-in-the-Loop 确认
"""

from app.sandbox.exceptions import (
    ConcurrentAccessError,
    PathTraversalError,
    SandboxError,
    SandboxTimeoutError,
)
from app.sandbox.risk_policy import RiskAssessment, RiskLevel, SecurityMode, UnifiedRiskPolicy
from app.sandbox.types import ExecutionRequest, ExecutionResult, SandboxType
from app.sandbox.workspace import AgentWorkspace, WorkspaceConfig

__all__ = [
    # Exceptions
    "SandboxError",
    "PathTraversalError",
    "ConcurrentAccessError",
    "SandboxTimeoutError",
    # Types
    "SandboxType",
    "ExecutionRequest",
    "ExecutionResult",
    # Risk Policy
    "RiskLevel",
    "RiskAssessment",
    "UnifiedRiskPolicy",
    "SecurityMode",
    # Workspace
    "AgentWorkspace",
    "WorkspaceConfig",
]
