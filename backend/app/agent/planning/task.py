"""
Task 数据结构 - Planning Layer 核心数据模型

设计原则：
- 与前端 WorkflowGraph 的 Node 结构对齐
- 支持 DAG 依赖关系
- 支持 SSE 序列化
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    """任务状态 - 与前端 Node.status 对齐"""
    PENDING = "pending"      # 灰色 - 等待执行
    RUNNING = "running"      # 黄色 - 执行中
    SUCCESS = "success"      # 绿色 - 成功
    ERROR = "error"          # 红色 - 失败
    SKIPPED = "skipped"      # 跳过


@dataclass
class Task:
    """
    原子化任务 - Planning Layer 的基本单元

    设计原则：
    - 单一职责：一个 Task 只做一件事
    - 可验证：有明确的 acceptance_criteria
    - 可重试：失败后可以重新执行
    - 与前端对齐：字段与 WorkflowGraph.Node 对应
    """
    id: str
    title: str
    description: str

    # 依赖关系 (DAG 边)
    depends_on: list[str] = field(default_factory=list)

    # 执行状态
    status: TaskStatus = TaskStatus.PENDING

    # 完成条件 (LLM 可验证)
    acceptance_criteria: str = ""

    # 工具提示 (建议使用的工具)
    tools_hint: list[str] = field(default_factory=list)

    # 执行元数据
    started_at: datetime | None = None
    completed_at: datetime | None = None
    output: str | None = None
    error_message: str | None = None

    # 重试机制
    retry_count: int = 0
    max_retries: int = 3

    # 是否可选 (失败时可跳过)
    is_optional: bool = False

    def can_start(self, completed_task_ids: set[str]) -> bool:
        """检查任务是否可以开始执行"""
        if self.status != TaskStatus.PENDING:
            return False
        # 所有依赖都已完成
        return all(dep_id in completed_task_ids for dep_id in self.depends_on)

    def mark_running(self) -> None:
        """标记为执行中"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()

    def mark_success(self, output: str = "") -> None:
        """标记为成功"""
        self.status = TaskStatus.SUCCESS
        self.completed_at = datetime.now()
        self.output = output

    def mark_error(self, error: str) -> None:
        """标记为失败"""
        self.status = TaskStatus.ERROR
        self.completed_at = datetime.now()
        self.error_message = error
        self.retry_count += 1

    def mark_skipped(self) -> None:
        """标记为跳过"""
        self.status = TaskStatus.SKIPPED
        self.completed_at = datetime.now()

    def can_retry(self) -> bool:
        """检查是否可以重试"""
        return self.status == TaskStatus.ERROR and self.retry_count < self.max_retries

    def reset_for_retry(self) -> None:
        """重置任务状态用于重试"""
        self.status = TaskStatus.PENDING
        self.started_at = None
        self.completed_at = None
        self.error_message = None

    @property
    def duration_ms(self) -> int | None:
        """执行时长 (毫秒)"""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds() * 1000)
        return None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典 (用于 SSE 序列化)"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "dependsOn": self.depends_on,  # 驼峰命名，与前端对齐
            "acceptanceCriteria": self.acceptance_criteria,
            "toolsHint": self.tools_hint,
            "metadata": {
                "startTime": int(self.started_at.timestamp() * 1000) if self.started_at else None,
                "endTime": int(self.completed_at.timestamp() * 1000) if self.completed_at else None,
                "duration": self.duration_ms,
                "output": self.output,
                "errorMessage": self.error_message,
            }
        }


@dataclass
class Plan:
    """
    执行计划 - Task DAG 容器

    包含多个 Task，通过 depends_on 形成 DAG
    """
    id: str
    goal: str
    tasks: list[Task] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1  # 重规划时递增

    def get_task(self, task_id: str) -> Task | None:
        """获取指定任务"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def get_completed_task_ids(self) -> set[str]:
        """获取已完成的任务 ID 集合"""
        return {
            t.id for t in self.tasks
            if t.status in (TaskStatus.SUCCESS, TaskStatus.SKIPPED)
        }

    def get_ready_tasks(self) -> list[Task]:
        """获取所有可执行的任务 (依赖已满足)"""
        completed_ids = self.get_completed_task_ids()
        return [t for t in self.tasks if t.can_start(completed_ids)]

    def get_running_tasks(self) -> list[Task]:
        """获取正在执行的任务"""
        return [t for t in self.tasks if t.status == TaskStatus.RUNNING]

    def get_failed_tasks(self) -> list[Task]:
        """获取失败的任务"""
        return [t for t in self.tasks if t.status == TaskStatus.ERROR]

    def is_complete(self) -> bool:
        """检查计划是否完成 (所有任务成功或跳过)"""
        return all(
            t.status in (TaskStatus.SUCCESS, TaskStatus.SKIPPED)
            for t in self.tasks
        )

    def is_blocked(self) -> bool:
        """检查计划是否被阻塞 (有失败且无法继续)"""
        if self.is_complete():
            return False
        # 有失败任务且没有可执行任务
        has_failed = any(t.status == TaskStatus.ERROR for t in self.tasks)
        has_ready = bool(self.get_ready_tasks())
        return has_failed and not has_ready

    def get_progress(self) -> dict[str, Any]:
        """获取进度统计"""
        total = len(self.tasks)
        completed = len([t for t in self.tasks if t.status == TaskStatus.SUCCESS])
        failed = len([t for t in self.tasks if t.status == TaskStatus.ERROR])
        running = len([t for t in self.tasks if t.status == TaskStatus.RUNNING])
        skipped = len([t for t in self.tasks if t.status == TaskStatus.SKIPPED])
        pending = total - completed - failed - running - skipped

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "skipped": skipped,
            "pending": pending,
            "percentage": int(100 * (completed + skipped) / total) if total > 0 else 0,
        }

    def to_dict(self) -> dict[str, Any]:
        """转换为字典 (用于 SSE 序列化)"""
        return {
            "planId": self.id,
            "goal": self.goal,
            "version": self.version,
            "tasks": [t.to_dict() for t in self.tasks],
            "progress": self.get_progress(),
            "createdAt": int(self.created_at.timestamp() * 1000),
            "updatedAt": int(self.updated_at.timestamp() * 1000),
        }


class ReplanDecision(str, Enum):
    """重规划决策"""
    RETRY = "retry"           # 重试当前任务
    SKIP = "skip"             # 跳过当前任务
    REPLAN = "replan"         # 重新规划
    ABORT = "abort"           # 终止执行
    HUMAN = "human"           # 人工介入
