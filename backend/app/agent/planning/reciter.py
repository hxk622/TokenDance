"""
PlanReciter - Plan Recitation 生成器

核心职责：
- 每轮将结构化 Plan 追加到 Context 末尾
- 防止 LLM 在长 Context 中遗忘目标 (Lost-in-the-Middle)
- 提醒 LLM 当前任务和完成条件

设计原则：
- 简洁明了，不浪费 Token
- 突出当前任务和下一步
- 包含 acceptance_criteria 让 LLM 知道何时算完成
"""

from .scheduler import TaskScheduler
from .task import Plan, Task, TaskStatus


class PlanReciter:
    """
    Plan Recitation 生成器

    用于：
    - 在每轮 LLM 调用前生成 Plan 摘要
    - 追加到 Context 末尾，提醒 LLM 当前目标
    """

    # Recitation 最多显示的任务数
    MAX_COMPLETED_TASKS = 3
    MAX_BLOCKED_TASKS = 2

    def generate(self, plan: Plan, scheduler: TaskScheduler) -> str:
        """
        生成 Plan Recitation 文本

        Args:
            plan: 当前 Plan
            scheduler: TaskScheduler 实例

        Returns:
            str: Recitation 文本，追加到 Context 末尾
        """
        progress = plan.get_progress()
        current_task = scheduler.current_task
        ready_tasks = scheduler.get_ready_tasks()
        blocked_tasks = scheduler.get_blocked_tasks()

        # 构建 Recitation
        lines = [
            "",
            "---",
            "",
            f"🎯 **Goal**: {plan.goal}",
            "",
            f"**Progress**: {progress['completed']}/{progress['total']} tasks "
            f"({progress['percentage']}%)",
            "",
        ]

        # 已完成任务 (最多显示 N 个)
        completed = [t for t in plan.tasks if t.status == TaskStatus.SUCCESS]
        if completed:
            lines.append("**Completed**:")
            for task in completed[-self.MAX_COMPLETED_TASKS:]:
                lines.append(f"  ✅ {task.title}")
            if len(completed) > self.MAX_COMPLETED_TASKS:
                lines.append(f"  ... and {len(completed) - self.MAX_COMPLETED_TASKS} more")
            lines.append("")

        # 当前任务 (最重要)
        if current_task:
            lines.extend(self._format_current_task(current_task))
        elif ready_tasks:
            # 没有正在执行的任务，但有准备好的任务
            lines.append("**Next Task**:")
            next_task = ready_tasks[0]
            lines.append(f"  ⏳ {next_task.title}")
            if next_task.description:
                lines.append(f"     {next_task.description[:100]}")
            if next_task.acceptance_criteria:
                lines.append(f"     *Acceptance*: {next_task.acceptance_criteria}")
            lines.append("")

        # 被阻塞的任务
        if blocked_tasks:
            lines.append("**Blocked**:")
            for task in blocked_tasks[:self.MAX_BLOCKED_TASKS]:
                deps = ", ".join(task.depends_on)
                lines.append(f"  ⏸️ {task.title} (waiting for: {deps})")
            if len(blocked_tasks) > self.MAX_BLOCKED_TASKS:
                lines.append(f"  ... and {len(blocked_tasks) - self.MAX_BLOCKED_TASKS} more")
            lines.append("")

        # 强调当前焦点
        if current_task:
            lines.append(f"⚠️ **FOCUS on \"{current_task.title}\" until acceptance criteria is met!**")
        elif ready_tasks:
            lines.append(f"⚠️ **Start \"{ready_tasks[0].title}\" next!**")

        lines.append("")
        lines.append("---")

        return "\n".join(lines)

    def _format_current_task(self, task: Task) -> list[str]:
        """格式化当前正在执行的任务"""
        lines = [
            "**Current Task**:",
            f"  🔄 {task.title}",
        ]

        if task.description:
            # 限制描述长度
            desc = task.description[:150]
            if len(task.description) > 150:
                desc += "..."
            lines.append(f"     {desc}")

        if task.acceptance_criteria:
            lines.append(f"     *Acceptance*: {task.acceptance_criteria}")

        if task.tools_hint:
            lines.append(f"     *Suggested tools*: {', '.join(task.tools_hint)}")

        lines.append("")
        return lines

    def generate_minimal(self, plan: Plan, scheduler: TaskScheduler) -> str:
        """
        生成最小化的 Recitation (Token 紧张时使用)

        Args:
            plan: 当前 Plan
            scheduler: TaskScheduler 实例

        Returns:
            str: 简短的 Recitation 文本
        """
        progress = plan.get_progress()
        current = scheduler.current_task

        if current:
            return (
                f"[Plan: {progress['completed']}/{progress['total']}] "
                f"Current: {current.title}"
            )

        ready = scheduler.get_ready_tasks()
        if ready:
            return (
                f"[Plan: {progress['completed']}/{progress['total']}] "
                f"Next: {ready[0].title}"
            )

        return f"[Plan: {progress['completed']}/{progress['total']}]"
