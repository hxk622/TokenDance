"""
Plan SSE Events - Plan 相关 SSE 事件发射

用于将 PlanningLayer 的状态同步到前端 WorkflowGraph
"""

from typing import Any

from app.agent.types import SSEEvent, SSEEventType

from .task import Plan, Task


class PlanEventEmitter:
    """
    Plan SSE 事件发射器

    负责：
    - 发射 Plan 创建/修改事件
    - 发射 Task 状态变更事件
    - 与前端 WorkflowGraph 数据格式对齐
    """

    @staticmethod
    def plan_created(plan: Plan) -> SSEEvent:
        """
        发射 Plan 创建事件

        前端收到后初始化 WorkflowGraph
        """
        return SSEEvent(
            type=SSEEventType.PLAN_CREATED,
            data=plan.to_dict()
        )

    @staticmethod
    def plan_revised(plan: Plan, reason: str = "") -> SSEEvent:
        """
        发射 Plan 修订事件

        前端收到后重新渲染 WorkflowGraph
        """
        data = plan.to_dict()
        data["reason"] = reason
        return SSEEvent(
            type=SSEEventType.PLAN_REVISED,
            data=data
        )

    # ==================== AnyGen-style Planning/Step events ====================
    @staticmethod
    def planning_start(goal: str = "") -> SSEEvent:
        """
        发射 Planning 开始事件

        用于前端 PlanningCard 初始化
        """
        return SSEEvent(
            type=SSEEventType.PLANNING_START,
            data={
                "goal": goal,
                "title": "Planning",
            }
        )

    @staticmethod
    def planning_content(content: str) -> SSEEvent:
        """
        发射 Planning 内容事件

        支持流式追加
        """
        return SSEEvent(
            type=SSEEventType.PLANNING_CONTENT,
            data={
                "content": content,
            }
        )

    @staticmethod
    def planning_done() -> SSEEvent:
        """
        发射 Planning 完成事件
        """
        return SSEEvent(
            type=SSEEventType.PLANNING_DONE,
            data={"status": "done"}
        )

    @staticmethod
    def step_start(task: Task) -> SSEEvent:
        """
        发射 Step 开始事件 (用于 ExecutionTimeline)
        """
        return SSEEvent(
            type=SSEEventType.STEP_START,
            data={
                "step_id": task.id,
                "label": task.title,
                "icon": PlanEventEmitter._infer_step_icon(task),
            }
        )

    @staticmethod
    def step_update(step_id: str, label: str | None = None, content: str | None = None) -> SSEEvent:
        """
        发射 Step 更新事件
        """
        data: dict[str, Any] = {"step_id": step_id}
        if label is not None:
            data["label"] = label
        if content is not None:
            data["content"] = content
        return SSEEvent(
            type=SSEEventType.STEP_UPDATE,
            data=data
        )

    @staticmethod
    def step_done(task: Task, output: str | None = None) -> SSEEvent:
        """
        发射 Step 完成事件
        """
        data: dict[str, Any] = {
            "step_id": task.id,
            "status": "done",
        }
        if output:
            data["output"] = output
        return SSEEvent(
            type=SSEEventType.STEP_DONE,
            data=data
        )

    @staticmethod
    def step_failed(task: Task, error: str | None = None) -> SSEEvent:
        """
        发射 Step 失败事件
        """
        data: dict[str, Any] = {
            "step_id": task.id,
            "status": "failed",
        }
        if error:
            data["error"] = error
        return SSEEvent(
            type=SSEEventType.STEP_FAILED,
            data=data
        )

    @staticmethod
    def _infer_step_icon(task: Task) -> str:
        """
        推断 Step icon 类型 (与前端 StepIconType 对齐)
        """
        tools = [t.lower() for t in task.tools_hint]
        text = f"{task.title} {task.description}".lower()

        if any(t in tools for t in ["web_search", "search"]) or "search" in text or "搜索" in text:
            return "search"
        if any(t in tools for t in ["read_url", "read", "browser"]) or "read" in text or "阅读" in text:
            return "read"
        if "analy" in text or "分析" in text:
            return "analyze"
        if "write" in text or "draft" in text or "撰写" in text or "写" in text:
            return "write"
        if "plan" in text or "规划" in text:
            return "plan"

        return "tool"

    @staticmethod
    def task_start(task: Task) -> SSEEvent:
        """
        发射 Task 开始执行事件

        前端收到后将节点状态改为 running (黄色)
        """
        return SSEEvent(
            type=SSEEventType.TASK_START,
            data={
                "taskId": task.id,
                "status": "running",
                "startTime": int(task.started_at.timestamp() * 1000) if task.started_at else None,
            }
        )

    @staticmethod
    def task_complete(task: Task) -> SSEEvent:
        """
        发射 Task 完成事件

        前端收到后将节点状态改为 success (绿色)
        """
        return SSEEvent(
            type=SSEEventType.TASK_COMPLETE,
            data={
                "taskId": task.id,
                "status": "success",
                "output": task.output,
                "endTime": int(task.completed_at.timestamp() * 1000) if task.completed_at else None,
                "duration": task.duration_ms,
            }
        )

    @staticmethod
    def task_failed(task: Task) -> SSEEvent:
        """
        发射 Task 失败事件

        前端收到后将节点状态改为 error (红色)
        """
        return SSEEvent(
            type=SSEEventType.TASK_FAILED,
            data={
                "taskId": task.id,
                "status": "error",
                "errorMessage": task.error_message,
                "endTime": int(task.completed_at.timestamp() * 1000) if task.completed_at else None,
                "retryCount": task.retry_count,
                "canRetry": task.can_retry(),
            }
        )

    @staticmethod
    def task_update(task: Task) -> SSEEvent:
        """
        发射 Task 通用更新事件

        用于任何状态变更
        """
        return SSEEvent(
            type=SSEEventType.TASK_UPDATE,
            data=task.to_dict()
        )

    @staticmethod
    def progress_update(plan: Plan) -> SSEEvent:
        """
        发射进度更新事件

        用于前端显示整体进度条
        """
        progress = plan.get_progress()
        return SSEEvent(
            type=SSEEventType.RESEARCH_PROGRESS_UPDATE,  # 复用研究进度事件
            data={
                "phase": "executing",
                "phaseProgress": progress["percentage"],
                "overallProgress": progress["percentage"],
                "currentAction": f"Executing tasks ({progress['completed']}/{progress['total']})",
            }
        )


def create_plan_events_for_scheduler(emitter: PlanEventEmitter) -> dict[str, Any]:
    """
    为 TaskScheduler 创建回调函数

    Returns:
        dict: 包含 on_task_start, on_task_complete, on_task_failed 回调
    """
    events_queue: list[SSEEvent] = []

    def on_start(task: Task) -> None:
        events_queue.append(emitter.task_start(task))

    def on_complete(task: Task) -> None:
        events_queue.append(emitter.task_complete(task))

    def on_failed(task: Task, error: str) -> None:
        events_queue.append(emitter.task_failed(task))

    return {
        "on_task_start": on_start,
        "on_task_complete": on_complete,
        "on_task_failed": on_failed,
        "events_queue": events_queue,
    }
