"""
PlanManager - 计划管理器

.. deprecated:: 2026-01
    此模块已废弃，请使用新的 Planning 组件代替：

    新架构组件：
    - Task, Plan, TaskStatus from `app.agent.planning.task`
    - TaskScheduler from `app.agent.planning.scheduler`
    - AtomicPlanner from `app.agent.planning.planner`
    - PlanReciter from `app.agent.planning.reciter`

    迁移指南：
    1. Task 数据结构已统一，使用新的 `app.agent.planning.task.Task`
    2. Plan 调度用 TaskScheduler 代替 get_next_tasks()
    3. 三文件工作法由 AgentEngine 直接管理

    在 AgentEngine 中使用：
    - engine.run_stream_with_planning() 已集成完整的 Planning 流程

核心功能：
1. 原子化任务拆分
2. Plan生成和更新
3. 依赖关系管理
4. 与三文件工作法集成
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from app.agent.working_memory import ThreeFilesManager


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Task:
    """
    原子化任务

    设计原则：
    - 单一职责
    - 可独立验证
    - 失败时可重试
    """
    id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    depends_on: list[str] = field(default_factory=list)  # 依赖的任务ID列表
    tools_needed: list[str] = field(default_factory=list)  # 需要的工具
    estimated_time: int | None = None  # 预计时间（分钟）
    actual_time: int | None = None  # 实际时间（分钟）
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    retry_count: int = 0
    max_retries: int = 3

    def can_start(self, completed_task_ids: list[str]) -> bool:
        """
        检查任务是否可以开始

        Args:
            completed_task_ids: 已完成的任务ID列表

        Returns:
            bool: 是否可以开始
        """
        if self.status != TaskStatus.PENDING:
            return False

        # 检查依赖是否都已完成
        for dep_id in self.depends_on:
            if dep_id not in completed_task_ids:
                return False

        return True

    def mark_started(self):
        """标记任务开始"""
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.now()

    def mark_completed(self):
        """标记任务完成"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        if self.started_at:
            self.actual_time = int((self.completed_at - self.started_at).total_seconds() / 60)

    def mark_failed(self, error: str):
        """标记任务失败"""
        self.status = TaskStatus.FAILED
        self.error_message = error
        self.retry_count += 1

    def can_retry(self) -> bool:
        """检查是否可以重试"""
        return self.status == TaskStatus.FAILED and self.retry_count < self.max_retries

    def reset_for_retry(self):
        """重置任务用于重试"""
        self.status = TaskStatus.PENDING
        self.started_at = None
        self.completed_at = None


@dataclass
class Plan:
    """
    执行计划

    包含多个原子化任务，支持依赖关系
    """
    id: str
    goal: str
    tasks: list[Task] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: str = "active"  # active/completed/failed

    def get_task(self, task_id: str) -> Task | None:
        """获取任务"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def get_next_tasks(self) -> list[Task]:
        """
        获取下一步可执行的任务

        Returns:
            List[Task]: 可执行的任务列表
        """
        completed_ids = [t.id for t in self.tasks if t.status == TaskStatus.COMPLETED]

        next_tasks = []
        for task in self.tasks:
            if task.can_start(completed_ids):
                next_tasks.append(task)

        return next_tasks

    def get_progress(self) -> dict[str, Any]:
        """
        获取计划进度

        Returns:
            dict: 进度信息
        """
        total = len(self.tasks)
        completed = len([t for t in self.tasks if t.status == TaskStatus.COMPLETED])
        failed = len([t for t in self.tasks if t.status == TaskStatus.FAILED])
        in_progress = len([t for t in self.tasks if t.status == TaskStatus.IN_PROGRESS])

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "pending": total - completed - failed - in_progress,
            "completion_rate": completed / total if total > 0 else 0,
        }

    def to_markdown(self) -> str:
        """
        转换为Markdown格式（用于task_plan.md）

        Returns:
            str: Markdown文本
        """
        md_lines = [
            f"# Task Plan: {self.goal}",
            "",
            "## 目标",
            self.goal,
            "",
            "## 任务列表",
            ""
        ]

        # 按依赖关系分组任务
        for i, task in enumerate(self.tasks, 1):
            status_icon = {
                TaskStatus.COMPLETED: "✅",
                TaskStatus.IN_PROGRESS: "🔄",
                TaskStatus.FAILED: "❌",
                TaskStatus.PENDING: "⏳",
                TaskStatus.SKIPPED: "⏭️",
            }.get(task.status, "❓")

            md_lines.append(f"### Task {i}: {task.title} {status_icon}")
            md_lines.append(f"**ID**: {task.id}")
            md_lines.append(f"**描述**: {task.description}")
            md_lines.append(f"**状态**: {task.status.value}")

            if task.depends_on:
                md_lines.append(f"**依赖**: {', '.join(task.depends_on)}")

            if task.tools_needed:
                md_lines.append(f"**所需工具**: {', '.join(task.tools_needed)}")

            if task.error_message:
                md_lines.append(f"**错误**: {task.error_message}")

            md_lines.append("")

        # 进度统计
        progress = self.get_progress()
        md_lines.extend([
            "## 进度统计",
            f"- 总任务数: {progress['total']}",
            f"- 已完成: {progress['completed']}",
            f"- 进行中: {progress['in_progress']}",
            f"- 失败: {progress['failed']}",
            f"- 待处理: {progress['pending']}",
            f"- 完成率: {progress['completion_rate']:.1%}",
        ])

        return "\n".join(md_lines)


class PlanManager:
    """
    计划管理器

    负责：
    1. 生成执行计划
    2. 原子化任务拆分
    3. 管理任务执行流程
    4. 与三文件工作法集成
    """

    def __init__(self, three_files: ThreeFilesManager):
        """
        初始化PlanManager

        Args:
            three_files: ThreeFilesManager实例
        """
        self.three_files = three_files
        self.current_plan: Plan | None = None

    def create_plan(self, goal: str, tasks: list[Task]) -> Plan:
        """
        创建新计划

        Args:
            goal: 目标描述
            tasks: 任务列表

        Returns:
            Plan: 计划对象
        """
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        plan = Plan(
            id=plan_id,
            goal=goal,
            tasks=tasks,
        )

        self.current_plan = plan

        # 写入task_plan.md
        self._sync_to_file()

        return plan

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        error: str | None = None
    ):
        """
        更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态
            error: 错误消息（如果失败）
        """
        if not self.current_plan:
            raise ValueError("No active plan")

        task = self.current_plan.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        # 更新状态
        if status == TaskStatus.IN_PROGRESS:
            task.mark_started()
        elif status == TaskStatus.COMPLETED:
            task.mark_completed()
            # 记录到progress.md
            self.three_files.update_progress(
                f"✅ 完成任务: {task.title}"
            )
        elif status == TaskStatus.FAILED:
            task.mark_failed(error or "Unknown error")
            # 记录错误到progress.md
            self.three_files.update_progress(
                f"❌ 任务失败: {task.title}\n错误: {error}",
                is_error=True
            )

        # 同步到文件
        self._sync_to_file()

    def get_next_task(self) -> Task | None:
        """
        获取下一个可执行的任务

        Returns:
            Task: 下一个任务，如果没有则返回None
        """
        if not self.current_plan:
            return None

        next_tasks = self.current_plan.get_next_tasks()
        return next_tasks[0] if next_tasks else None

    def retry_failed_task(self, task_id: str):
        """
        重试失败的任务

        Args:
            task_id: 任务ID
        """
        if not self.current_plan:
            raise ValueError("No active plan")

        task = self.current_plan.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        if not task.can_retry():
            raise ValueError(f"Task cannot be retried: {task_id}")

        task.reset_for_retry()
        self._sync_to_file()

    def _sync_to_file(self):
        """同步当前计划到task_plan.md"""
        if not self.current_plan:
            return

        markdown = self.current_plan.to_markdown()
        self.three_files.update_task_plan(markdown, append=False)

    def load_plan_from_file(self) -> Plan | None:
        """
        从task_plan.md加载计划

        Returns:
            Plan: 计划对象，如果解析失败返回None
        """
        # 简化实现：从文件读取但不解析
        # 完整实现需要Markdown解析器
        self.three_files.read_task_plan()
        # TODO: 实现Markdown解析逻辑
        return self.current_plan

    def get_plan_summary(self) -> str:
        """
        获取计划摘要（用于Plan Recitation）

        Returns:
            str: 计划摘要
        """
        if not self.current_plan:
            return "No active plan"

        progress = self.current_plan.get_progress()
        next_task = self.get_next_task()

        summary = f"""
# Current Plan Summary (Plan Recitation)

**Goal**: {self.current_plan.goal}

**Progress**: {progress['completed']}/{progress['total']} tasks completed ({progress['completion_rate']:.0%})

**Next Task**: {next_task.title if next_task else 'None (all tasks done or blocked)'}

**Tasks Overview**:
"""

        for task in self.current_plan.tasks[:5]:  # 只显示前5个任务
            status_icon = {
                TaskStatus.COMPLETED: "✅",
                TaskStatus.IN_PROGRESS: "🔄",
                TaskStatus.FAILED: "❌",
                TaskStatus.PENDING: "⏳",
            }.get(task.status, "❓")
            summary += f"- {status_icon} {task.title}\n"

        if len(self.current_plan.tasks) > 5:
            summary += f"... and {len(self.current_plan.tasks) - 5} more tasks\n"

        return summary
