# -*- coding: utf-8 -*-
"""
Research Agents 模块

Multi-Agent 架构实现:
- BaseResearchAgent: Agent 基类
- 专业化 Agents (Searcher, Reader, Analyst, Verifier, Synthesizer)
- ResearchOrchestrator: 研究编排器
"""

from .base import (
    # 角色和状态
    AgentRole,
    TaskStatus,
    TaskPriority,
    # 数据结构
    AgentTask,
    AgentResult,
    HandoffMessage,
    # 基类和协议
    BaseResearchAgent,
    HandoffProtocol,
    TaskFactory,
)

from .agents import (
    SearcherAgent,
    ReaderAgent,
    AnalystAgent,
    VerifierAgent,
    SynthesizerAgent,
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
