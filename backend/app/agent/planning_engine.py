"""
PlanningAgentEngine - 带完整 Planning 流程的 Agent Engine

实现统一架构：
- TaskScheduler 控制流程（代码决定做什么）
- LLM 负责内容生成（模型决定怎么做）
- SSE 事件同步到前端 WorkflowGraph

核心流程：
1. AtomicPlanner 生成 Plan (Task DAG)
2. TaskScheduler 调度任务执行
3. 每轮 Plan Recitation 防止遗忘
4. SSE 推送状态到前端
"""

from collections.abc import AsyncGenerator
from typing import Any

from app.agent.llm.base import BaseLLM, LLMMessage
from app.agent.planning import (
    AtomicPlanner,
    Plan,
    PlanEventEmitter,
    PlanReciter,
    ReplanDecision,
    SimplePlanBuilder,
    Task,
    TaskScheduler,
)
from app.agent.types import SSEEvent, SSEEventType
from app.core.logging import get_logger
from app.filesystem import AgentFileSystem

logger = get_logger(__name__)


class PlanningAgentEngine:
    """
    带完整 Planning 流程的 Agent Engine

    核心设计：
    - 流程控制权归代码（TaskScheduler）
    - 内容生成权归模型（LLM）
    - 每步可验证、可重试、可恢复

    使用方式：
        engine = PlanningAgentEngine(llm, filesystem, ...)
        async for event in engine.run_stream("帮我写一份市场分析报告"):
            # 处理 SSE 事件
            print(event.type, event.data)
    """

    def __init__(
        self,
        llm: BaseLLM,
        filesystem: AgentFileSystem,
        workspace_id: str,
        session_id: str,
        max_iterations: int = 50,
    ):
        self.llm = llm
        self.filesystem = filesystem
        self.workspace_id = workspace_id
        self.session_id = session_id
        self.max_iterations = max_iterations

        # Planning 组件
        self.planner = AtomicPlanner(llm)
        self.scheduler = TaskScheduler()
        self.reciter = PlanReciter()
        self.event_emitter = PlanEventEmitter()

        # 状态
        self.iteration_count = 0
        self._plan: Plan | None = None

    async def run_stream(self, user_goal: str) -> AsyncGenerator[SSEEvent, None]:
        """
        流式运行 Agent，返回 SSE 事件流

        Args:
            user_goal: 用户目标

        Yields:
            SSEEvent: 各类事件（plan.created, task.start, task.complete, etc.）
        """
        logger.info("=== Planning Agent Run Started ===")
        logger.info(f"Goal: {user_goal}")

        try:
            # Phase 1: Planning
            yield SSEEvent(
                type=SSEEventType.STATUS,
                data={"phase": "planning", "message": "正在分析任务并制定计划..."}
            )

            # 生成 Plan
            self._plan = await self.planner.plan(user_goal)
            self.scheduler.load_plan(self._plan)

            # 推送 Plan 创建事件
            yield self.event_emitter.plan_created(self._plan)

            logger.info(f"Plan created: {self._plan.id} with {len(self._plan.tasks)} tasks")

            # Phase 2: Execution Loop
            yield SSEEvent(
                type=SSEEventType.STATUS,
                data={"phase": "executing", "message": "开始执行任务..."}
            )

            while not self.scheduler.is_complete():
                self.iteration_count += 1

                if self.iteration_count > self.max_iterations:
                    logger.warning(f"Max iterations reached: {self.max_iterations}")
                    break

                # 2.1 获取可执行任务
                ready_tasks = self.scheduler.get_ready_tasks()

                if not ready_tasks:
                    # 没有可执行任务，检查是否阻塞
                    if self.scheduler.is_blocked():
                        logger.error("Plan is blocked - no tasks can proceed")
                        yield SSEEvent(
                            type=SSEEventType.ERROR,
                            data={"message": "任务执行被阻塞，可能需要人工介入"}
                        )
                        break
                    continue

                # 2.2 执行第一个准备好的任务
                task = ready_tasks[0]

                async for event in self._execute_task(task):
                    yield event

                # 2.3 发送进度更新
                yield self.event_emitter.progress_update(self._plan)

            # Phase 3: Completion
            if self._plan.is_complete():
                yield SSEEvent(
                    type=SSEEventType.DONE,
                    data={
                        "status": "success",
                        "message": "所有任务执行完成",
                        "iterations": self.iteration_count,
                        "progress": self._plan.get_progress()
                    }
                )
            else:
                yield SSEEvent(
                    type=SSEEventType.DONE,
                    data={
                        "status": "incomplete",
                        "message": "任务未完全完成",
                        "iterations": self.iteration_count,
                        "progress": self._plan.get_progress()
                    }
                )

        except Exception as e:
            logger.error(f"Planning agent error: {e}", exc_info=True)
            yield SSEEvent(
                type=SSEEventType.ERROR,
                data={"message": str(e), "type": e.__class__.__name__}
            )

    async def _execute_task(self, task: Task) -> AsyncGenerator[SSEEvent, None]:
        """
        执行单个 Task

        这是"LLM 只负责如何完成这个原子任务"的体现
        """
        logger.info(f"Executing task: {task.title} ({task.id})")

        # 标记任务开始
        self.scheduler.start_task(task.id)
        yield self.event_emitter.task_start(task)

        # 生成 Plan Recitation
        assert self._plan is not None, "Plan must be initialized before execution"
        recitation = self.reciter.generate(self._plan, self.scheduler)

        try:
            # 调用 LLM 执行任务
            # 这里 LLM 只负责"如何完成这个特定任务"，而不是"接下来做什么"
            prompt = self._build_task_prompt(task, recitation)

            yield SSEEvent(
                type=SSEEventType.THINKING,
                data={"content": f"正在执行: {task.title}...\n"}
            )

            response = await self.llm.complete(
                messages=[LLMMessage(role="user", content=prompt)],
                system=self._get_task_system_prompt(task),
            )

            # 检查是否完成
            output = response.content

            # TODO: 这里应该验证 acceptance_criteria
            # 目前简化处理，假设执行成功

            # 标记任务完成
            self.scheduler.complete_task(task.id, output[:500])
            yield self.event_emitter.task_complete(task)

            yield SSEEvent(
                type=SSEEventType.CONTENT,
                data={"content": f"\n✅ {task.title} 完成\n"}
            )

        except Exception as e:
            logger.error(f"Task execution failed: {e}")

            # 标记任务失败
            failed_task, decision = self.scheduler.fail_task(task.id, str(e))
            yield self.event_emitter.task_failed(task)

            yield SSEEvent(
                type=SSEEventType.ERROR,
                data={
                    "message": f"任务 '{task.title}' 执行失败: {e}",
                    "taskId": task.id,
                    "decision": decision.value
                }
            )

            # 根据决策处理
            if decision == ReplanDecision.RETRY:
                yield SSEEvent(
                    type=SSEEventType.THINKING,
                    data={"content": f"正在重试任务: {task.title}...\n"}
                )
            elif decision == ReplanDecision.REPLAN:
                yield SSEEvent(
                    type=SSEEventType.THINKING,
                    data={"content": "正在重新规划...\n"}
                )
                # 触发重规划
                assert self._plan is not None, "Plan must exist to replan"
                new_plan = await self.planner.replan(self._plan, task, str(e))
                self.scheduler.replace_plan(new_plan)
                self._plan = new_plan
                yield self.event_emitter.plan_revised(new_plan, str(e))

    def _build_task_prompt(self, task: Task, recitation: str) -> str:
        """构建任务执行 Prompt"""
        return f"""Please complete the following task:

## Task: {task.title}

{task.description}

## Acceptance Criteria:
{task.acceptance_criteria or "Complete the task as described."}

## Suggested Tools:
{', '.join(task.tools_hint) if task.tools_hint else "Use your best judgment."}

---
{recitation}
---

Please complete this task now. Focus ONLY on this specific task."""

    def _get_task_system_prompt(self, task: Task) -> str:
        """获取任务执行的 System Prompt"""
        return f"""You are an AI assistant executing a specific task within a larger plan.

Your current task is: {task.title}

Rules:
1. Focus ONLY on completing this specific task
2. Do NOT try to do other tasks or plan ahead
3. Use the suggested tools if available
4. Complete the task according to the acceptance criteria
5. Be concise and efficient

If you cannot complete the task, explain why clearly."""

    def get_plan(self) -> Plan | None:
        """获取当前 Plan"""
        return self._plan

    def get_progress(self) -> dict[str, Any]:
        """获取当前进度"""
        if self._plan:
            return self._plan.get_progress()
        return {"total": 0, "completed": 0, "percentage": 0}


# 便捷函数：创建简单的研究任务 Plan
def create_research_plan(topic: str) -> Plan:
    """
    创建一个研究任务的 Plan 模板

    用于快速测试，不需要调用 LLM
    """
    builder = SimplePlanBuilder()

    builder.set_goal(f"完成关于 '{topic}' 的研究报告")

    builder.add_task(
        title="搜索相关信息",
        description=f"使用网络搜索收集关于 '{topic}' 的基本信息",
        acceptance_criteria="找到至少 3 条相关信息源",
        tools_hint=["web_search"],
    )

    builder.add_task(
        title="阅读详细内容",
        description="深入阅读搜索结果中的关键来源",
        acceptance_criteria="从至少 2 个来源提取关键信息",
        depends_on=["t1"],
        tools_hint=["read_url"],
    )

    builder.add_task(
        title="整合分析",
        description="整合收集的信息，分析关键发现",
        acceptance_criteria="形成对主题的综合理解",
        depends_on=["t2"],
    )

    builder.add_task(
        title="撰写报告",
        description="根据分析结果撰写结构化报告",
        acceptance_criteria="完成包含摘要、主体、结论的报告",
        depends_on=["t3"],
        tools_hint=["file_ops"],
    )

    return builder.build()
