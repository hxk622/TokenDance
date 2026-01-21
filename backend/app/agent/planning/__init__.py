"""
Planning模块 - 统一任务规划层

核心组件：
- Task, Plan: 数据结构 (与前端 WorkflowGraph 对齐)
- TaskScheduler: DAG 调度器 (流程控制权归代码)
- AtomicPlanner: LLM 生成 Plan (内容生成权归模型)
- PlanReciter: Plan Recitation 防止遗忘

设计原则：
- 大模型在"宏观逻辑"上60%成功率，在"微观动作"上99.9%成功率
- 工程核心：把1个60%成功率的大任务切碎成100个99.9%成功率的小任务
- 流程控制权归代码，内容生成权归模型
"""

# 核心数据结构
# SSE 事件
from .events import PlanEventEmitter

# 旧接口兼容 (deprecated - 将在2026-03移除)
# 请使用上方的新组件代替
from .plan_manager import PlanManager  # noqa: F401 (deprecated)

# 规划器
from .planner import AtomicPlanner, SimplePlanBuilder

# Plan Recitation
from .reciter import PlanReciter

# 调度器
from .scheduler import TaskScheduler
from .task import Plan, ReplanDecision, Task, TaskStatus

__all__ = [
    # 核心数据结构
    "Task",
    "TaskStatus",
    "Plan",
    "ReplanDecision",
    # 调度器
    "TaskScheduler",
    # Recitation
    "PlanReciter",
    # 规划器
    "AtomicPlanner",
    "SimplePlanBuilder",
    # SSE 事件
    "PlanEventEmitter",
    # 旧接口
    "PlanManager",
]
