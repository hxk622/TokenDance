"""
AtomicPlanner - 原子化任务规划器

核心职责：
- 将用户目标拆分为原子化 Task DAG
- 使用 LLM 生成结构化 Plan
- 代码验证 DAG 合法性 (无环、依赖存在)

设计原则：
- LLM 负责"生成什么内容"
- 代码负责"验证是否合法"
- 每个 Task 必须有明确的 acceptance_criteria
"""

import json
import uuid
from typing import Any, cast

from app.agent.llm.base import BaseLLM, LLMMessage
from app.agent.validator import get_validation_level_for_domain
from app.core.logging import get_logger

from .task import Plan, Task, TaskStatus

logger = get_logger(__name__)


# LLM 生成 Plan 的 Prompt
PLAN_GENERATION_PROMPT = '''You are a task planning assistant. Your job is to break down a user's goal into atomic, executable tasks.

## Rules for Task Decomposition:
1. **Atomic**: Each task should do ONE thing only
2. **Verifiable**: Each task must have clear acceptance criteria
3. **Independent**: Tasks should be as independent as possible
4. **Ordered**: Define dependencies between tasks (what must complete before what)

## Task Structure:
Each task must have:
- `id`: Unique identifier (e.g., "t1", "t2")
- `title`: Short name (5-10 words)
- `description`: What needs to be done (1-2 sentences)
- `acceptance_criteria`: How to know it's done (specific, measurable)
- `depends_on`: List of task IDs that must complete first (empty [] if none)
- `tools_hint`: Suggested tools to use (e.g., ["web_search", "read_url"])

## Available Tools:
- web_search: Search the web for information
- read_url: Read content from a specific URL
- file_ops: Read/write files
- shell: Execute shell commands
- browser_screenshot: Take screenshot of a webpage

## Output Format:
Return a JSON object with:
```json
{{
  "goal": "Restate the user's goal",
  "tasks": [
    {{
      "id": "t1",
      "title": "Task title",
      "description": "What to do",
      "acceptance_criteria": "How to verify completion",
      "depends_on": [],
      "tools_hint": ["web_search"]
    }}
  ]
}}
```

## User's Goal:
{goal}

## Context (if any):
{context}

Now generate the task plan as JSON:'''


REPLAN_PROMPT = '''The previous plan failed. You need to create a revised plan.

## Previous Plan:
{previous_plan}

## Failure Information:
- Failed Task: {failed_task}
- Error: {error}
- Completed Tasks: {completed_tasks}

## Rules:
1. Keep completed tasks as-is (don't redo them)
2. Modify or add tasks to work around the failure
3. Consider alternative approaches
4. If the original approach is fundamentally flawed, suggest a different strategy

## Output the revised plan as JSON (same format as before):'''


class AtomicPlanner:
    """
    原子化任务规划器

    使用 LLM 生成结构化的 Task DAG，代码验证合法性
    """

    def __init__(self, llm: BaseLLM) -> None:
        self.llm = llm

    async def plan(self, goal: str, context: str = "") -> Plan:
        """
        为用户目标生成执行计划

        Args:
            goal: 用户目标
            context: 额外上下文信息

        Returns:
            Plan: 包含原子化 Task 的执行计划
        """
        logger.info(f"Generating plan for goal: {goal[:100]}...")

        # 1. 调用 LLM 生成计划
        prompt = PLAN_GENERATION_PROMPT.format(goal=goal, context=context or "None")

        response = await self.llm.complete(
            messages=[LLMMessage(role="user", content=prompt)],
            system="You are a precise task planner. Output only valid JSON.",
        )

        # 2. 解析 JSON
        plan_data = self._parse_json_response(response.content)

        # 3. 构建 Plan 对象
        plan = self._build_plan(plan_data)

        # 4. 验证 DAG 合法性
        self._validate_plan(plan)

        logger.info(f"Plan generated: {plan.id} with {len(plan.tasks)} tasks")
        return plan

    async def replan(
        self,
        previous_plan: Plan,
        failed_task: Task,
        error: str
    ) -> Plan:
        """
        基于失败信息重新规划

        Args:
            previous_plan: 之前的计划
            failed_task: 失败的任务
            error: 错误信息

        Returns:
            Plan: 修订后的计划
        """
        logger.info(f"Replanning after failure: {failed_task.title}")

        # 构建重规划 prompt
        completed_tasks = [
            t.title for t in previous_plan.tasks
            if t.status == TaskStatus.SUCCESS
        ]

        prompt = REPLAN_PROMPT.format(
            previous_plan=json.dumps(previous_plan.to_dict(), indent=2),
            failed_task=f"{failed_task.title}: {failed_task.description}",
            error=error,
            completed_tasks=", ".join(completed_tasks) if completed_tasks else "None"
        )

        response = await self.llm.complete(
            messages=[LLMMessage(role="user", content=prompt)],
            system="You are a precise task planner. Output only valid JSON.",
        )

        # 解析并构建新计划
        plan_data = self._parse_json_response(response.content)
        new_plan = self._build_plan(plan_data)

        # 继承版本号
        new_plan.version = previous_plan.version + 1

        self._validate_plan(new_plan)

        logger.info(f"Replan complete: version {new_plan.version}")
        return new_plan

    def _parse_json_response(self, content: str) -> dict[str, Any]:
        """解析 LLM 返回的 JSON"""
        # 尝试提取 JSON 块
        content = content.strip()

        # 处理 markdown 代码块
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            content = content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            content = content[start:end].strip()

        try:
            return cast(dict[str, Any], json.loads(content))
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Content: {content[:500]}")
            raise ValueError(f"Invalid JSON response from LLM: {e}") from e

    def _build_plan(self, data: dict[str, Any]) -> Plan:
        """从解析后的数据构建 Plan 对象"""
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        goal = data.get("goal", "")

        # 根据 goal 内容检测 validation_level
        default_validation_level = get_validation_level_for_domain(goal)
        logger.debug(f"Default validation level for plan: {default_validation_level.value}")

        tasks: list[Task] = []
        for task_data in data.get("tasks", []):
            # 支持从 JSON 中读取 validation_level，否则使用默认值
            validation_level = task_data.get(
                "validation_level",
                default_validation_level.value
            )

            task = Task(
                id=task_data.get("id", f"t{len(tasks)+1}"),
                title=task_data.get("title", "Untitled Task"),
                description=task_data.get("description", ""),
                acceptance_criteria=task_data.get("acceptance_criteria", ""),
                depends_on=task_data.get("depends_on", []),
                tools_hint=task_data.get("tools_hint", []),
                status=TaskStatus.PENDING,
                validation_level=validation_level,
            )
            tasks.append(task)

        return Plan(
            id=plan_id,
            goal=goal,
            tasks=tasks,
        )

    def _validate_plan(self, plan: Plan) -> None:
        """验证 Plan 的 DAG 合法性"""
        task_ids = {t.id for t in plan.tasks}

        # 1. 检查依赖是否存在
        for task in plan.tasks:
            for dep_id in task.depends_on:
                if dep_id not in task_ids:
                    raise ValueError(
                        f"Task '{task.id}' depends on non-existent task '{dep_id}'"
                    )

        # 2. 检查是否有环 (拓扑排序)
        if self._has_cycle(plan):
            raise ValueError("Plan contains circular dependencies")

        # 3. 检查是否有至少一个入口节点 (无依赖)
        entry_tasks = [t for t in plan.tasks if not t.depends_on]
        if not entry_tasks:
            raise ValueError("Plan has no entry point (all tasks have dependencies)")

        logger.info(f"Plan validated: {len(plan.tasks)} tasks, {len(entry_tasks)} entry points")

    def _has_cycle(self, plan: Plan) -> bool:
        """检测 DAG 是否有环 (使用 DFS)"""
        # 状态: 0=未访问, 1=访问中, 2=已完成
        state: dict[str, int] = {t.id: 0 for t in plan.tasks}

        # 构建邻接表
        adj: dict[str, list[str]] = {t.id: [] for t in plan.tasks}
        for task in plan.tasks:
            for dep_id in task.depends_on:
                adj[dep_id].append(task.id)  # dep -> task 的边

        def dfs(node: str) -> bool:
            if state[node] == 1:  # 正在访问，发现环
                return True
            if state[node] == 2:  # 已完成，跳过
                return False

            state[node] = 1  # 标记为访问中

            for neighbor in adj[node]:
                if dfs(neighbor):
                    return True

            state[node] = 2  # 标记为已完成
            return False

        # 从所有节点开始 DFS
        for task_id in state:
            if state[task_id] == 0:
                if dfs(task_id):
                    return True

        return False


# 简单任务的快速 Plan 生成器 (不需要调用 LLM)
class SimplePlanBuilder:
    """
    简单 Plan 构建器

    用于已知任务结构的场景，不需要调用 LLM
    """

    def __init__(self) -> None:
        self._tasks: list[Task] = []
        self._goal: str = ""

    def set_goal(self, goal: str) -> "SimplePlanBuilder":
        """设置目标"""
        self._goal = goal
        return self

    def add_task(
        self,
        title: str,
        description: str = "",
        acceptance_criteria: str = "",
        depends_on: list[str] | None = None,
        tools_hint: list[str] | None = None,
        is_optional: bool = False,
    ) -> "SimplePlanBuilder":
        """添加任务"""
        task_id = f"t{len(self._tasks) + 1}"
        task = Task(
            id=task_id,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria,
            depends_on=depends_on or [],
            tools_hint=tools_hint or [],
            is_optional=is_optional,
        )
        self._tasks.append(task)
        return self

    def build(self) -> Plan:
        """构建 Plan"""
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        return Plan(
            id=plan_id,
            goal=self._goal,
            tasks=self._tasks.copy(),
        )
