"""
Agent 实现模块

包含各种类型的 Agent 实现：
- BasicAgent: 简单对话
- ResearchAgent: 研究型 Agent（支持工具调用）
- DeepResearchAgent: 深度研究 Agent（多轮搜索、报告生成）
- PPTAgent: PPT 生成 Agent（大纲生成、内容填充、渲染导出）
- CodeAgent: 代码生成（待实现）
- PlanAgent: 计划执行（待实现）
"""
from .basic import BasicAgent, create_basic_agent
from .deep_research import DeepResearchAgent, create_deep_research_agent
from .ppt import PPTAgent, create_ppt_agent
from .research import ResearchAgent, create_research_agent

__all__ = [
    "BasicAgent",
    "create_basic_agent",
    "ResearchAgent",
    "create_research_agent",
    "DeepResearchAgent",
    "create_deep_research_agent",
    "PPTAgent",
    "create_ppt_agent",
]
