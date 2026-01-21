"""
TaskExecutor - 原子任务执行器

核心职责：
- 执行单个 Task 的完整生命周期
- 状态机驱动的执行循环
- 工具调用 + 结果观察
- 失败检测 + 自动重试
- 验收条件验证

设计原则：
- 可复用：Direct 模式和 Planning 模式都使用这个执行器
- 可观测：通过 SSE 事件流输出执行过程
- 可中断：支持超时和手动取消
"""

import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any, Literal

from app.agent.execution_context import ExecutionContext
from app.agent.executor import ToolCall, ToolCallExecutor, ToolResult
from app.agent.failure import FailureObserver, FailureSignal
from app.agent.llm.base import BaseLLM, LLMMessage
from app.agent.planning.task import Task
from app.agent.types import SSEEvent, SSEEventType
from app.agent.validator import TaskValidator, ValidationLevel, ValidationResult
from app.core.logging import get_logger

logger = get_logger(__name__)


# ========== 数据结构 ==========


@dataclass
class TaskResult:
    """任务执行结果"""
    status: Literal["success", "failed", "timeout", "skipped"]
    output: str = ""
    error: str | None = None
    duration_ms: int = 0
    tool_calls_count: int = 0
    iterations: int = 0

    def is_success(self) -> bool:
        return self.status == "success"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "tool_calls_count": self.tool_calls_count,
            "iterations": self.iterations,
        }


@dataclass
class TaskExecutorConfig:
    """执行器配置"""
    max_iterations: int = 10  # 单个 Task 最大迭代次数
    timeout_seconds: float = 300.0  # 超时时间
    max_retries_per_tool: int = 3  # 单个工具最大重试次数
    enable_tool_calls: bool = True  # 是否启用工具调用
    stream_events: bool = True  # 是否流式输出事件
    enable_validation: bool = True  # 是否启用任务验证
    max_validation_retries: int = 1  # 验证失败后最大重试次数


# ========== Prompts ==========


TASK_EXECUTION_SYSTEM_PROMPT = """You are an AI assistant executing a specific task.

## Rules:
1. Focus ONLY on completing the assigned task
2. Use tools when necessary to accomplish the task
3. Verify your work against the acceptance criteria
4. When the task is complete, wrap your final response in <task_done> tags

## Task Completion:
When you have completed the task successfully, respond with:
<task_done>
[Summary of what was accomplished]
</task_done>

## If you cannot complete the task:
Explain clearly what went wrong and what would be needed to complete it.

## Available Output Formats:
- For tool calls: Use <tool_use> tags
- For completion: Use <task_done> tags
- For reasoning: Use <reasoning> tags (optional)
"""


def build_task_prompt(task: Task, context: ExecutionContext) -> str:
    """构建任务执行 Prompt"""
    # 获取最近的消息历史 (最多 10 条)
    recent_messages = context.get_last_n_messages(10)
    history_text = ""
    if recent_messages:
        history_lines = []
        for msg in recent_messages:
            role_label = msg.role.upper()
            content_preview = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            history_lines.append(f"[{role_label}]: {content_preview}")
        history_text = "\n".join(history_lines)

    # 获取全局变量
    variables_text = ""
    if context.variables:
        var_lines = [f"- {k}: {v}" for k, v in context.variables.items()]
        variables_text = "\n".join(var_lines)

    prompt = f"""## Task: {task.title}

### Description:
{task.description}

### Acceptance Criteria:
{task.acceptance_criteria or "Complete the task as described."}

### Suggested Tools:
{', '.join(task.tools_hint) if task.tools_hint else "Use your best judgment."}
"""

    if history_text:
        prompt += f"""
### Recent Context:
{history_text}
"""

    if variables_text:
        prompt += f"""
### Available Data:
{variables_text}
"""

    prompt += """
---
Please complete this task now. When done, wrap your response in <task_done> tags.
"""

    return prompt


# ========== TaskExecutor ==========


class TaskExecutor:
    """
    原子任务执行器

    核心能力：
    1. 状态机驱动的执行循环
    2. 工具调用 + 结果观察
    3. 失败检测 + 自动重试
    4. 验收条件验证

    使用示例：
    ```python
    executor = TaskExecutor(llm, tool_executor, failure_observer)
    result = await executor.execute(task, context)

    # 或者流式执行
    async for event in executor.execute_stream(task, context):
        yield event
    ```
    """

    def __init__(
        self,
        llm: BaseLLM,
        tool_executor: ToolCallExecutor,
        failure_observer: FailureObserver | None = None,
        config: TaskExecutorConfig | None = None,
    ):
        """
        初始化 TaskExecutor

        Args:
            llm: LLM 客户端
            tool_executor: 工具调用执行器
            failure_observer: 失败观察器 (可选)
            config: 执行器配置
        """
        self.llm = llm
        self.tool_executor = tool_executor
        self.failure_observer = failure_observer or FailureObserver()
        self.config = config or TaskExecutorConfig()

        # 初始化验证器
        self.validator = TaskValidator(llm)

        # 执行状态
        self._current_task: Task | None = None
        self._iteration_count: int = 0
        self._tool_calls_count: int = 0
        self._validation_retries: int = 0
        self._start_time: float = 0

    # ========== 同步执行 ==========

    async def execute(
        self,
        task: Task,
        context: ExecutionContext,
    ) -> TaskResult:
        """
        执行单个任务 (非流式)

        Args:
            task: 要执行的原子任务
            context: 执行上下文

        Returns:
            TaskResult: 任务执行结果
        """
        result: TaskResult | None = None

        async for event in self.execute_stream(task, context):
            if event.type == SSEEventType.DONE:
                # 从 DONE 事件中提取结果
                data = event.data or {}
                result = TaskResult(
                    status=data.get("status", "failed"),
                    output=data.get("output", ""),
                    error=data.get("error"),
                    duration_ms=data.get("duration_ms", 0),
                    tool_calls_count=data.get("tool_calls_count", 0),
                    iterations=data.get("iterations", 0),
                )

        return result or TaskResult(status="failed", error="No result returned")

    # ========== 流式执行 ==========

    async def execute_stream(
        self,
        task: Task,
        context: ExecutionContext,
    ) -> AsyncGenerator[SSEEvent, None]:
        """
        执行单个任务 (流式)

        Args:
            task: 要执行的原子任务
            context: 执行上下文

        Yields:
            SSEEvent: 执行过程事件
        """
        self._current_task = task
        self._iteration_count = 0
        self._tool_calls_count = 0
        self._start_time = time.perf_counter()

        logger.info(f"TaskExecutor starting: {task.title} ({task.id})")

        try:
            # 主执行循环
            while self._iteration_count < self.config.max_iterations:
                self._iteration_count += 1

                # 检查超时
                elapsed = time.perf_counter() - self._start_time
                if elapsed > self.config.timeout_seconds:
                    logger.warning(f"Task timeout: {task.title}")
                    yield self._make_done_event("timeout", error="Task execution timeout")
                    return

                # 1. 构建 Prompt
                prompt = build_task_prompt(task, context)

                # 2. 调用 LLM
                yield SSEEvent(
                    type=SSEEventType.THINKING,
                    data={"content": f"Iteration {self._iteration_count}: Thinking...\n"}
                )

                response = await self.llm.complete(
                    messages=[LLMMessage(role="user", content=prompt)],
                    system=TASK_EXECUTION_SYSTEM_PROMPT,
                )

                # 更新 token 统计
                if response.usage:
                    context.add_token_usage(
                        input_tokens=response.usage.get("input_tokens", 0),
                        output_tokens=response.usage.get("output_tokens", 0),
                    )

                # 添加到上下文
                context.add_assistant_message(response.content)

                # 3. 检查是否完成
                if self._is_task_complete(response.content):
                    output = self._extract_completion(response.content)
                    logger.info(f"Task completed: {task.title}")

                    # ========== 执行验证 ==========
                    if self.config.enable_validation:
                        async for event in self._validate_and_maybe_retry(
                            task, output, context
                        ):
                            if event.type == SSEEventType.DONE:
                                yield event
                                return
                            yield event
                        # 如果验证流程没有 yield DONE，继续执行循环进行重试
                        continue

                    yield self._make_done_event("success", output=output)
                    return

                # 4. 检查是否有工具调用
                if self.config.enable_tool_calls and self.tool_executor.has_tool_calls(response.content):
                    # 解析工具调用
                    tool_calls = self.tool_executor.parse_tool_calls(response.content)

                    if tool_calls:
                        # 发送工具调用事件
                        for tc in tool_calls:
                            yield SSEEvent(
                                type=SSEEventType.TOOL_CALL,
                                data={
                                    "tool_name": tc.tool_name,
                                    "parameters": tc.parameters,
                                }
                            )

                        # 执行工具
                        tool_results = await self.tool_executor.execute_all(tool_calls)
                        self._tool_calls_count += len(tool_results)

                        # 处理工具结果
                        should_stop, error = await self._handle_tool_results(
                            tool_calls, tool_results, context
                        )

                        # 发送工具结果事件
                        for tr in tool_results:
                            yield SSEEvent(
                                type=SSEEventType.TOOL_RESULT,
                                data={
                                    "tool_name": tr.tool_name,
                                    "success": tr.success,
                                    "result": tr.result if tr.success else None,
                                    "error": tr.error if not tr.success else None,
                                }
                            )

                        if should_stop:
                            logger.error(f"Task failed due to tool errors: {error}")
                            yield self._make_done_event("failed", error=error)
                            return

                        # 将工具结果注入到上下文
                        formatted_results = self.tool_executor.format_tool_results(tool_results)
                        context.add_user_message(f"Tool results:\n{formatted_results}")

                        continue

                # 5. 既没有完成标记也没有工具调用
                # 检查是否有 <answer> 标记 (兼容旧格式)
                if self.tool_executor.has_final_answer(response.content):
                    answer = self.tool_executor.extract_answer(response.content)
                    logger.info(f"Task completed with answer: {task.title}")
                    yield self._make_done_event("success", output=answer or response.content)
                    return

                # 继续下一轮迭代
                logger.debug(f"No completion marker, continuing iteration {self._iteration_count}")

            # 达到最大迭代次数
            logger.warning(f"Task reached max iterations: {task.title}")
            yield self._make_done_event("timeout", error=f"Reached max iterations ({self.config.max_iterations})")

        except Exception as e:
            logger.error(f"TaskExecutor error: {e}", exc_info=True)
            yield self._make_done_event("failed", error=str(e))

        finally:
            self._current_task = None

    # ========== 辅助方法 ==========

    async def _validate_and_maybe_retry(
        self,
        task: Task,
        output: str,
        context: ExecutionContext,
    ) -> AsyncGenerator[SSEEvent, None]:
        """
        验证任务结果，失败时触发重试

        Yields:
            SSEEvent: 验证事件，如果验证通过或达到最大重试次数，yield DONE 事件
        """
        # 解析验证级别
        try:
            level = ValidationLevel(task.validation_level)
        except ValueError:
            level = ValidationLevel.LIGHT

        # Level NONE/QUICK 跳过 LLM 验证
        if level in (ValidationLevel.NONE, ValidationLevel.QUICK):
            logger.debug(f"Skipping validation for task: {task.title} (level={level})")
            yield self._make_done_event("success", output=output)
            return

        # 发送验证开始事件
        yield SSEEvent(
            type=SSEEventType.VALIDATION_START,
            data={
                "task_id": task.id,
                "level": level.value,
            }
        )

        # 执行验证
        result = await self.validator.validate(
            task_title=task.title,
            task_description=task.description,
            acceptance_criteria=task.acceptance_criteria or "Complete the task as described",
            output=output,
            level=level,
        )

        # 发送验证结果事件
        yield SSEEvent(
            type=SSEEventType.VALIDATION_RESULT,
            data={
                "task_id": task.id,
                "passed": result.passed,
                "confidence": result.confidence,
                "reason": result.reason,
                "issues": result.issues,
            }
        )

        if result.passed:
            logger.info(f"Task validation passed: {task.title}")
            yield self._make_done_event("success", output=output)
            return

        # 验证失败
        logger.warning(f"Task validation failed: {task.title} - {result.issues}")

        # 检查是否还有重试次数
        if self._validation_retries >= self.config.max_validation_retries:
            logger.error(f"Task validation failed after {self._validation_retries} retries")
            yield self._make_done_event(
                "failed",
                output=output,
                error=f"Validation failed: {', '.join(result.issues)}"
            )
            return

        # 触发重试
        self._validation_retries += 1
        yield SSEEvent(
            type=SSEEventType.VALIDATION_RETRY,
            data={
                "task_id": task.id,
                "retry_count": self._validation_retries,
                "max_retries": self.config.max_validation_retries,
                "issues": result.issues,
            }
        )

        # 将验证反馈注入上下文，让 LLM 重新执行
        feedback = self._format_validation_feedback(result)
        context.add_user_message(feedback)
        # 不 yield DONE，让外层循环继续执行

    def _format_validation_feedback(self, result: ValidationResult) -> str:
        """格式化验证反馈"""
        lines = [
            "## Validation Failed",
            "",
            "Your previous output did not pass validation. Please address the following issues:",
            "",
        ]

        for i, issue in enumerate(result.issues, 1):
            lines.append(f"{i}. {issue}")

        if result.reason:
            lines.append("")
            lines.append(f"**Reason:** {result.reason}")

        lines.append("")
        lines.append("Please revise your approach and try again.")

        return "\n".join(lines)

    def _is_task_complete(self, response: str) -> bool:
        """检查任务是否完成"""
        return "<task_done>" in response

    def _extract_completion(self, response: str) -> str:
        """提取完成信息"""
        import re
        match = re.search(r"<task_done>(.*?)</task_done>", response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response

    async def _handle_tool_results(
        self,
        tool_calls: list[ToolCall],
        tool_results: list[ToolResult],
        context: ExecutionContext,
    ) -> tuple[bool, str | None]:
        """
        处理工具执行结果

        Returns:
            (should_stop, error_message)
        """
        for tc, tr in zip(tool_calls, tool_results, strict=False):
            if not tr.success:
                # 创建失败信号
                signal = FailureSignal.from_tool_result(
                    tool_name=tc.tool_name,
                    success=False,
                    error=tr.error,
                    tool_args=tc.parameters,
                )

                # 观察失败
                self.failure_observer.observe(signal)

                # 检查是否应该停止重试
                if self.failure_observer.should_stop_retry(signal):
                    return True, f"Tool '{tc.tool_name}' failed after multiple retries: {tr.error}"

                # 记录到上下文
                context.add_tool_result(tc.tool_name, tr.error or "Unknown error", success=False)
            else:
                # 成功的工具调用
                context.add_tool_result(tc.tool_name, tr.result, success=True)

        return False, None

    def _make_done_event(
        self,
        status: Literal["success", "failed", "timeout", "skipped"],
        output: str = "",
        error: str | None = None,
    ) -> SSEEvent:
        """创建完成事件"""
        elapsed_ms = int((time.perf_counter() - self._start_time) * 1000)

        return SSEEvent(
            type=SSEEventType.DONE,
            data={
                "status": status,
                "output": output,
                "error": error,
                "duration_ms": elapsed_ms,
                "tool_calls_count": self._tool_calls_count,
                "iterations": self._iteration_count,
            }
        )

    # ========== 状态查询 ==========

    def get_current_task(self) -> Task | None:
        """获取当前正在执行的任务"""
        return self._current_task

    def get_iteration_count(self) -> int:
        """获取当前迭代次数"""
        return self._iteration_count

    def get_tool_calls_count(self) -> int:
        """获取工具调用次数"""
        return self._tool_calls_count
