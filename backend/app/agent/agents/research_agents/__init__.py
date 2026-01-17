"""
Research Agents 模块

Multi-Agent 架构实现:
- BaseResearchAgent: Agent 基类
- 专业化 Agents (Searcher, Reader, Analyst, Verifier, Synthesizer)
- ResearchOrchestrator: 研究编排器
"""

from .agents import (
    AnalystAgent,
    ReaderAgent,
    SearcherAgent,
    SynthesizerAgent,
    VerifierAgent,
)
from .base import (
    AgentResult,
    # 角色和状态
    AgentRole,
    # 数据结构
    AgentTask,
    # 基类和协议
    BaseResearchAgent,
    HandoffMessage,
    HandoffProtocol,
    TaskFactory,
    TaskPriority,
    TaskStatus,
)
from .orchestrator import (
    ResearchOrchestrator,
    ResearchPhase,
    ResearchPlan,
    ResearchState,
    TerminationReason,
)

__all__ = [
    # Base
    "AgentRole",
    "TaskStatus",
    "TaskPriority",
    "AgentTask",
    "AgentResult",
    "HandoffMessage",
    "BaseResearchAgent",
    "HandoffProtocol",
    "TaskFactory",
    # Agents
    "SearcherAgent",
    "ReaderAgent",
    "AnalystAgent",
    "VerifierAgent",
    "SynthesizerAgent",
    # Orchestrator
    "ResearchOrchestrator",
    "ResearchPhase",
    "ResearchPlan",
    "ResearchState",
    "TerminationReason",
]
