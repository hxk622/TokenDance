"""
TaskScheduler - DAG 调度器

核心职责：
- 管理 Plan 的执行流程
- 根据依赖关系确定可执行任务
- 处理任务完成/失败回调
- 决定重试/跳过/重规划

设计原则：
- 流程控制权归代码，不归 LLM
- 确定性调度，可预测行为
"""

from collections.abc import Callable
from datetime import datetime
from typing import Any

from app.core.logging import get_logger

from .task import Plan, ReplanDecision, Task, TaskStatus

logger = get_logger(__name__)


class TaskScheduler:
    """
    Task DAG 调度器

    核心职责：
    1. 加载并管理 Plan
    2. 根据依赖关系返回可执行任务
    3. 处理任务状态变更
    4. 决定失败后的处理策略
    """

    MAX_REPLAN_COUNT = 3  # 最大重规划次数

    def __init__(self) -> None:
        self._plan: Plan | None = None
        self._replan_count: int = 0
        self._current_task: Task | None = None

        # 回调函数
        self._on_task_start: Callable[[Task], None] | None = None
        self._on_task_complete: Callable[[Task], None] | None = None
        self._on_task_failed: Callable[[Task, str], None] | None = None
        self._on_plan_complete: Callable[[Plan], None] | None = None

    @property
    def plan(self) -> Plan | None:
        """当前加载的 Plan"""
        return self._plan

    @property
    def current_task(self) -> Task | None:
        """当前正在执行的任务"""
        return self._current_task

    def load_plan(self, plan: Plan) -> None:
        """加载新的 Plan"""
        self._plan = plan
        self._current_task = None
        logger.info(f"Plan loaded: {plan.id} with {len(plan.tasks)} tasks")

    def replace_plan(self, new_plan: Plan) -> None:
        """替换 Plan (重规划时使用)"""
        if self._plan:
            new_plan.version = self._plan.version + 1
        self._plan = new_plan
        self._current_task = None
        self._replan_count += 1
        logger.info(f"Plan replaced: version {new_plan.version}, replan count: {self._replan_count}")

    def is_complete(self) -> bool:
        """检查计划是否完成"""
        if not self._plan:
            return True
        return self._plan.is_complete()

    def is_blocked(self) -> bool:
        """检查计划是否被阻塞"""
        if not self._plan:
            return False
        return self._plan.is_blocked()

    def get_ready_tasks(self) -> list[Task]:
        """获取所有可执行的任务 (依赖已满足)"""
        if not self._plan:
            return []
        return self._plan.get_ready_tasks()

    def get_next_task(self) -> Task | None:
        """获取下一个要执行的任务 (单任务模式)"""
        ready = self.get_ready_tasks()
        return ready[0] if ready else None

    def start_task(self, task_id: str) -> Task | None:
        """开始执行任务"""
        if not self._plan:
            return None

        task = self._plan.get_task(task_id)
        if not task:
            logger.error(f"Task not found: {task_id}")
            return None

        if task.status != TaskStatus.PENDING:
            logger.warning(f"Task {task_id} is not pending, current status: {task.status}")
            return None

        task.mark_running()
        self._current_task = task
        self._plan.updated_at = datetime.now()

        logger.info(f"Task started: {task.title} ({task_id})")

        if self._on_task_start:
            self._on_task_start(task)

        return task

    def complete_task(self, task_id: str, output: str = "") -> Task | None:
        """标记任务完成"""
        if not self._plan:
            return None

        task = self._plan.get_task(task_id)
        if not task:
            logger.error(f"Task not found: {task_id}")
            return None

        task.mark_success(output)
        self._plan.updated_at = datetime.now()

        if self._current_task and self._current_task.id == task_id:
            self._current_task = None

        logger.info(f"Task completed: {task.title} ({task_id})")

        if self._on_task_complete:
            self._on_task_complete(task)

        # 检查 Plan 是否完成
        if self._plan.is_complete() and self._on_plan_complete:
            self._on_plan_complete(self._plan)

        return task

    def fail_task(self, task_id: str, error: str) -> tuple[Task | None, ReplanDecision]:
        """标记任务失败，并返回处理决策"""
        if not self._plan:
            return None, ReplanDecision.ABORT

        task = self._plan.get_task(task_id)
        if not task:
            logger.error(f"Task not found: {task_id}")
            return None, ReplanDecision.ABORT

        task.mark_error(error)
        self._plan.updated_at = datetime.now()

        if self._current_task and self._current_task.id == task_id:
            self._current_task = None

        logger.warning(f"Task failed: {task.title} ({task_id}), error: {error}")

        if self._on_task_failed:
            self._on_task_failed(task, error)

        # 决策逻辑
        decision = self._decide_on_failure(task)
        logger.info(f"Failure decision for {task_id}: {decision.value}")

        return task, decision

    def _decide_on_failure(self, task: Task) -> ReplanDecision:
        """决定失败后的处理策略"""

        # Level 1: 可重试
        if task.can_retry():
            task.reset_for_retry()
            return ReplanDecision.RETRY

        # Level 2: 可选任务可跳过
        if task.is_optional:
            task.mark_skipped()
            return ReplanDecision.SKIP

        # Level 3: 重规划
        if self._replan_count < self.MAX_REPLAN_COUNT:
            return ReplanDecision.REPLAN

        # Level 4: 需要人工介入
        return ReplanDecision.HUMAN

    def retry_task(self, task_id: str) -> Task | None:
        """重试任务"""
        if not self._plan:
            return None

        task = self._plan.get_task(task_id)
        if not task:
            return None

        if not task.can_retry():
            logger.warning(f"Task {task_id} cannot be retried")
            return None

        task.reset_for_retry()
        self._plan.updated_at = datetime.now()

        logger.info(f"Task reset for retry: {task.title} ({task_id})")
        return task

    def skip_task(self, task_id: str) -> Task | None:
        """跳过任务"""
        if not self._plan:
            return None

        task = self._plan.get_task(task_id)
        if not task:
            return None

        task.mark_skipped()
        self._plan.updated_at = datetime.now()

        logger.info(f"Task skipped: {task.title} ({task_id})")
        return task

    def get_progress(self) -> dict[str, Any]:
        """获取当前进度"""
        if not self._plan:
            return {"total": 0, "completed": 0, "percentage": 0}
        return self._plan.get_progress()

    def get_blocked_tasks(self) -> list[Task]:
        """获取被阻塞的任务 (依赖未完成)"""
        if not self._plan:
            return []

        self._plan.get_completed_task_ids()
        {t.id for t in self._plan.get_running_tasks()}
        ready_ids = {t.id for t in self.get_ready_tasks()}

        return [
            t for t in self._plan.tasks
            if t.status == TaskStatus.PENDING
            and t.id not in ready_ids
        ]

    # ========== 回调注册 ==========

    def on_task_start(self, callback: Callable[[Task], None]) -> None:
        """注册任务开始回调"""
        self._on_task_start = callback

    def on_task_complete(self, callback: Callable[[Task], None]) -> None:
        """注册任务完成回调"""
        self._on_task_complete = callback

    def on_task_failed(self, callback: Callable[[Task, str], None]) -> None:
        """注册任务失败回调"""
        self._on_task_failed = callback

    def on_plan_complete(self, callback: Callable[[Plan], None]) -> None:
        """注册计划完成回调"""
        self._on_plan_complete = callback

    # ========== 调试辅助 ==========

    def get_state_summary(self) -> dict[str, Any]:
        """获取调度器状态摘要 (调试用)"""
        if not self._plan:
            return {"status": "no_plan"}

        return {
            "plan_id": self._plan.id,
            "plan_version": self._plan.version,
            "replan_count": self._replan_count,
            "current_task": self._current_task.id if self._current_task else None,
            "progress": self.get_progress(),
            "is_complete": self.is_complete(),
            "is_blocked": self.is_blocked(),
            "ready_tasks": [t.id for t in self.get_ready_tasks()],
            "blocked_tasks": [t.id for t in self.get_blocked_tasks()],
        }
