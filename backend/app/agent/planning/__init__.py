"""
Planning模块 - 计划管理

核心功能：
- 原子化任务拆分（大任务→小任务）
- Plan验证和修订
- 与三文件工作法集成
- Plan Recitation（目标背诵）

设计原则：
- 大模型在"宏观逻辑"上60%成功率，在"微观动作"上99.9%成功率
- 工程核心：把1个60%成功率的大任务切碎成100个99.9%成功率的小任务
"""

from .plan_manager import PlanManager, Task, Plan

__all__ = [
    "PlanManager",
    "Task",
    "Plan",
]
