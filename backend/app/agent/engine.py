"""
Agent Engine - 核心执行循环 (状态机驱动)

实现铁律一：Agent = 状态机 + LLM 决策器

核心设计原则：
1. **状态机驱动**: 显式状态 + 确定性转移
2. **Append-Only Context**: 消息只追加，不修改
3. **Plan Recitation**: 每轮末尾追加 TODO 清单
4. **Keep the Failures**: 保留错误记录
5. **FailureSignal**: exit code 是最诚实的老师

参考文档：docs/architecture/Agent-Runtime-Design.md
"""

import asyncio
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.agent.context_manager import ContextManager
from app.agent.context_manager import Message as CtxMessage
from app.agent.executor import ToolCallExecutor
from app.agent.failure import (
    ExitCode,
    FailureObserver,
    FailureSignal,
)
from app.agent.failure.pattern_kb import FailurePatternKB

# Root cause analysis & pattern KB
from app.agent.failure.root_cause import RootCauseAnalyzer
from app.agent.feedback.loop import FeedbackLoop
from app.agent.hybrid_execution_prompts import (
    HYBRID_EXECUTION_SYSTEM_PROMPT,
)
from app.agent.llm.base import BaseLLM, LLMMessage, LLMResponse

# Distributed memory & feedback
from app.agent.long_memory.distributed import DistributedMemory, Lesson

# Planning System (Unified Architecture)
from app.agent.planning import (
    AtomicPlanner,
    Plan,
    PlanEventEmitter,
    PlanReciter,
    ReplanDecision,
    Task,
    TaskScheduler,
)

# Policies (Dynamic iteration, compression, token budget)
from app.agent.policies import (
    ContextCompressor,
    DynamicIterationPolicy,
    TokenBudgetManager,
)
from app.agent.prompts import ERROR_RECOVERY_PROMPT, FINDINGS_REMINDER_PROMPT

# 状态机和失败信号系统 (铁律一 + 铁律四)
from app.agent.state import (
    AgentState,
    Signal,
    StateMachine,
)

# Strategy adaptation
from app.agent.strategy.adaptation import StrategyAdaptation
from app.agent.tools.registry import ToolRegistry
from app.agent.types import SSEEvent, SSEEventType
from app.agent.working_memory.three_files import ThreeFilesManager
from app.context.unified_context import (
    ExecutionStatus,
    ExecutionType,
    get_unified_context,
)
from app.core.logging import get_logger
from app.filesystem import AgentFileSystem
from app.mcp.executor import (
    get_mcp_executor,
)

# Phase 2: Hybrid Execution imports
from app.routing.router import (
    ExecutionPath,
    get_execution_router,
)

# Skill System imports
from app.skills import (
    SkillLoader,
    SkillMatch,
    get_skill_executor,
    get_skill_matcher,
    get_skill_registry,
)

logger = get_logger(__name__)


@dataclass
class AgentResponse:
    """Agent 响应"""
    answer: str
    reasoning: str | None = None
    tool_calls: list[dict] | None = None
    token_usage: dict[str, int] | None = None
    iterations: int = 0


class AgentEngine:
    """
    Agent 核心引擎 (状态机驱动)

    实现五条铁律：
    1. **铁律一**: Agent = 状态机 + LLM 决策器
    2. **铁律二**: 架构决定成功率上限，不是模型
    3. **铁律三**: 工具是世界接口，不是插件 (4+2 核心工具)
    4. **铁律四**: 智能来自失败，不来自理解 (FailureSignal)
    5. **铁律五**: PolicyLayer 架构 (WorkState + ActionSpace + FailureSignal + ControlLoop)

    运行时规则：
    - **Append-Only Context**: 消息只追加，不修改
    - **Plan Recitation**: 每轮末尾追加 TODO 清单
    - **Keep the Failures**: 保留错误记录
    - **2-Action Rule**: 每2次搜索操作后记录 findings
    - **3-Strike Protocol**: 同类错误3次触发重读计划
    """

    def __init__(
        self,
        llm: BaseLLM,
        filesystem: AgentFileSystem,
        workspace_id: str,
        session_id: str,
        max_iterations: int = 20,  # legacy fallback; dynamic policy preferred
        enable_skills: bool = True,
    ):
        """
        初始化 Agent Engine

        Args:
            llm: LLM 客户端
            filesystem: 文件系统
            workspace_id: Workspace ID
            session_id: Session ID
            max_iterations: 最大迭代次数
            enable_skills: 是否启用 Skill 系统（默认 True）
        """
        self.llm = llm
        self.filesystem = filesystem
        self.workspace_id = workspace_id
        self.session_id = session_id
        self.max_iterations = max_iterations
        self.enable_skills = enable_skills

        # 初始化工具注册表
        self.tool_registry = ToolRegistry()

        # 初始化三文件管理器
        self.three_files = ThreeFilesManager(filesystem=filesystem, session_id=session_id)

        # 初始化 Context Manager
        self.context_manager = ContextManager(
            tool_registry=self.tool_registry,
            three_files=self.three_files,
            session_id=session_id
        )

        # 初始化 Executor
        self.executor = ToolCallExecutor(tool_registry=self.tool_registry)

        # =================================================================
        # 铁律一: 状态机
        # =================================================================
        self.state_machine = StateMachine(initial_state=AgentState.INIT)

        # =================================================================
        # 铁律四: 失败观察器
        # =================================================================
        self.failure_observer = FailureObserver()
        # 连接 progress.md 写入器 (Keep the Failures)
        self.failure_observer.set_progress_writer(
            lambda entry: self.three_files.update_progress(
                log_entry=entry, is_error=True
            )
        )
        # 注册失败回调（阶段2/3集成点）
        self.failure_observer.register_callback(lambda s: self._on_failure_signal(s))

        # 初始化 Skill 系统
        self.skill_registry = None
        self.skill_matcher = None
        self.skill_loader = None
        self.skill_executor = None

        if enable_skills:
            self._init_skill_system()

        # ========== Phase 2: Hybrid Execution System ==========
        # 初始化 ExecutionRouter 和 UnifiedExecutionContext
        self.execution_router = get_execution_router(
            skill_matcher=self.skill_matcher,
            skill_executor=self.skill_executor,
            skill_confidence_threshold=0.85,
            structured_task_confidence=0.70,
        )
        self.unified_context = get_unified_context(session_id=session_id)
        self.mcp_executor = get_mcp_executor()

        # 阶段2/3组件
        self.pattern_kb = FailurePatternKB(filesystem)
        self.root_cause_analyzer = RootCauseAnalyzer()
        self.strategy_adapter = StrategyAdaptation(self.execution_router)
        self.distributed_memory = DistributedMemory(filesystem)
        self.feedback_loop = FeedbackLoop(filesystem)

        # 状态
        self.iteration_count = 0
        self._current_skill_match: SkillMatch | None = None
        self._last_exit_code: int | None = None  # 铁律四: 记录最后退出码

        # =================================================================
        # Planning System (统一架构)
        # 流程控制权归代码（TaskScheduler）
        # 内容生成权归模型（LLM）
        # =================================================================
        self.planner = AtomicPlanner(llm)
        self.scheduler = TaskScheduler()
        self.plan_reciter = PlanReciter()
        self.plan_event_emitter = PlanEventEmitter()
        self._current_plan: Plan | None = None

        # -----------------------------------------------------------------
        # Policies: 动态迭代 / Context 压缩 / Token 预算
        # -----------------------------------------------------------------
        self.iteration_policy = DynamicIterationPolicy(
            base_budget=30,
            max_iterations=100,
            available_time_seconds=300.0,
            context_window_limit=self.context_manager.max_context_tokens,
        )
        self.context_compressor = ContextCompressor(
            context_window_limit=self.context_manager.max_context_tokens,
        )
        self.token_budget = TokenBudgetManager(
            total_budget=self.context_manager.max_context_tokens,
            reserved_ratio=0.20,
            min_iteration_budget=2000,
        )

        logger.info(
            f"Agent Engine initialized for session {session_id} "
            f"(skills={enable_skills}, state_machine=enabled, dynamic_policies=on)"
        )

    def _init_skill_system(self) -> None:
        """初始化 Skill 系统组件"""
        try:
            # 获取 Skill 注册表（全局单例）
            self.skill_registry = get_skill_registry()

            # 创建 Skill 匹配器（全局单例）
            self.skill_matcher = get_skill_matcher(self.skill_registry)

            # 创建 Skill 加载器
            self.skill_loader = SkillLoader(self.skill_registry)

            # 获取 Skill 执行器（全局单例）
            self.skill_executor = get_skill_executor(self.skill_registry)

            logger.info(
                f"Skill system initialized: {len(self.skill_registry)} skills available"
            )
        except Exception as e:
            logger.error(f"Failed to initialize skill system: {e}")
            self.enable_skills = False

    async def run(self, user_message: str) -> AgentResponse:
        """
        运行 Agent 主循环 (状态机驱动)

        铁律一实现：Agent = 状态机 + LLM 决策器
        状态转移由 Signal 驱动，而非简单的 while 循环

        Args:
            user_message: 用户输入

        Returns:
            AgentResponse: Agent 响应
        """
        logger.info("=== Agent Run Started (State Machine) ===")
        run_started_at = time.perf_counter()
        # 基于任务描述计算动态迭代预算（用于日志与监控）
        _ = self.iteration_policy.calculate_budget(user_message)
        logger.info(f"User message: {user_message}")
        logger.info(f"Initial state: {self.state_machine.current_state.value}")

        # 重置状态机到 INIT
        self.state_machine.reset()
        self.failure_observer.clear()
        self.iteration_count = 0

        # 发送 USER_MESSAGE_RECEIVED 信号 → 转移到 PARSING_INTENT
        self.state_machine.transition(Signal.USER_MESSAGE_RECEIVED)
        logger.info(f"State: {self.state_machine.current_state.value}")

        # Skill 匹配和注入
        await self._match_and_inject_skill(user_message)

        # 添加用户消息到 context
        self.context_manager.add_user_message(user_message)

        # 信号: 意图清晰 → 转移到 REASONING
        self.state_machine.transition(Signal.INTENT_CLEAR)
        logger.info(f"State: {self.state_machine.current_state.value}")

        # 保存最终推理结果
        last_reasoning: str | None = None

        # 状态机主循环
        while not self.state_machine.is_terminal():
            self.iteration_count += 1
            logger.info(f"--- Iteration {self.iteration_count} (State: {self.state_machine.current_state.value}) ---")

            # 动态继续条件检查（替代硬编码 max_iterations）
            tokens = self.context_manager.get_token_usage()
            elapsed = time.perf_counter() - run_started_at
            should_continue, reason = self.iteration_policy.should_continue(
                iteration=self.iteration_count,
                context_tokens_used=tokens.get("total", 0),
                has_fatal_error=False,
                elapsed_seconds=elapsed,
            )
            if not should_continue:
                logger.warning(f"Stopping due to policy: {reason} "
                               f"(elapsed={elapsed:.1f}s, tokens={tokens.get('total',0)})")
                self.state_machine.transition(Signal.MAX_ITERATIONS)
                break

            # 当接近上下文阈值时尝试压缩
            self._maybe_compress_context(tokens.get("total", 0))

            # 根据当前状态执行操作
            current_state = self.state_machine.current_state

            if current_state == AgentState.REASONING:
                # LLM 推理
                llm_response = await self._call_llm()

                # 添加 assistant 消息到 context
                self.context_manager.add_assistant_message(
                    content=llm_response.content,
                    metadata={"usage": llm_response.usage}
                )

                # 更新 token 使用量
                if llm_response.usage:
                    in_tok = llm_response.usage.get("input_tokens", 0)
                    out_tok = llm_response.usage.get("output_tokens", 0)
                    self.context_manager.update_token_usage(
                        input_tokens=in_tok,
                        output_tokens=out_tok,
                    )
                    # 同步到 TokenBudgetManager
                    self.token_budget.record_usage(in_tok, out_tok)

                    # 检查是否需要切换到摘要模式/压缩
                    switch, reason = self.token_budget.should_switch_to_summary_mode()
                    if switch:
                        logger.warning(f"Switching to summary mode: {reason}")
                        self._maybe_compress_context(
                            self.context_manager.get_token_usage().get("total", 0),
                            force_aggressive=True,
                        )

                # 提取推理过程
                last_reasoning = self.executor.extract_reasoning(llm_response.content)
                if last_reasoning:
                    logger.info(f"Reasoning: {last_reasoning[:200]}...")

                # 决策：检查 LLM 响应内容
                if self.executor.has_final_answer(llm_response.content):
                    # 有最终答案 → 发送 TASK_COMPLETE 信号
                    answer = self.executor.extract_answer(llm_response.content)
                    logger.info("Final answer received")
                    self._last_exit_code = ExitCode.SUCCESS.value
                    self.state_machine.transition(Signal.TASK_COMPLETE)

                    return AgentResponse(
                        answer=answer or llm_response.content,
                        reasoning=last_reasoning,
                        token_usage=self.context_manager.get_token_usage(),
                        iterations=self.iteration_count
                    )

                elif self.executor.has_tool_calls(llm_response.content):
                    # 需要工具 → 发送 NEED_TOOL 信号
                    self.state_machine.transition(Signal.NEED_TOOL)

                    # 解析工具调用
                    tool_calls = self.executor.parse_tool_calls(llm_response.content)
                    logger.info(f"Parsed {len(tool_calls)} tool calls")

                    # 执行工具 (进入 TOOL_CALLING 状态)
                    tool_results = await self.executor.execute_all(tool_calls)

                    # 处理工具结果
                    await self._handle_tool_results(tool_calls, tool_results)

                    # 格式化并添加工具结果到 context
                    tool_results_text = self.executor.format_tool_results(tool_results)
                    self.context_manager.add_tool_result_message(tool_results_text)

                    # 检查是否有 exit tool 调用
                    exit_result = self._check_exit_tool(tool_calls, tool_results)
                    if exit_result is not None:
                        self._last_exit_code = exit_result
                        if exit_result == ExitCode.SUCCESS.value:
                            self.state_machine.transition(Signal.EXIT_CODE_SUCCESS)
                        else:
                            self.state_machine.transition(Signal.EXIT_CODE_FAILURE)
                        continue

                    # 检查工具执行结果
                    all_success = all(r.success for r in tool_results)
                    if all_success:
                        self.state_machine.transition(Signal.TOOL_SUCCESS)
                    else:
                        # 检查是否触发 3-Strike
                        should_stop = any(
                            self.failure_observer.should_stop_retry(
                                FailureSignal.from_tool_result(
                                    tool_name=tc.tool_name,
                                    success=tr.success,
                                    error=tr.error,
                                    tool_args=tc.parameters,
                                )
                            )
                            for tc, tr in zip(tool_calls, tool_results, strict=False)
                            if not tr.success
                        )

                        if should_stop:
                            # 3-Strike 触发，进入 REFLECTING
                            self.state_machine.transition(Signal.TOOL_FAILED)
                        else:
                            self.state_machine.transition(Signal.TOOL_SUCCESS)

                else:
                    # 既没有答案也没有工具调用，返回内容
                    logger.warning("Response has neither answer nor tool calls")
                    self._last_exit_code = ExitCode.SUCCESS.value
                    self.state_machine.transition(Signal.TASK_COMPLETE)

                    return AgentResponse(
                        answer=llm_response.content,
                        reasoning=last_reasoning,
                        token_usage=self.context_manager.get_token_usage(),
                        iterations=self.iteration_count
                    )

            elif current_state == AgentState.TOOL_CALLING:
                # 工具已在 REASONING 状态执行，这里处理后续状态
                # 转移到 OBSERVING
                self.state_machine.transition(Signal.TOOL_SUCCESS)

            elif current_state == AgentState.OBSERVING:
                # 观察工具结果后，回到 REASONING 继续
                # 这个转移在 TOOL_SUCCESS 信号后自动发生
                pass

            elif current_state == AgentState.REFLECTING:
                # 反思状态：读取失败摘要，准备重新规划（阶段2集成）
                failure_summary = self.failure_observer.get_failure_summary_for_context()
                if failure_summary:
                    self.context_manager.add_user_message(
                        f"[System] 请根据以下失败记录调整策略:\n{failure_summary}"
                    )
                # 根因分析 + 策略自适应
                root = self.root_cause_analyzer.analyze(self.failure_observer.all_failures)
                if root:
                    strategies_text = "\n".join([f"- {s}" for s in root.strategies])
                    self.context_manager.add_user_message(
                        f"[Analyzer] 根因: {root.category} (置信度 {root.confidence:.2f})\n建议策略:\n{strategies_text}"
                    )
                    decision = self.strategy_adapter.apply(root)
                    # 记录到进度
                    self.three_files.update_progress(
                        log_entry=f"🧭 Strategy adapted: {decision.summary} ({decision.notes})",
                        is_error=False,
                    )
                # 转移到重新规划
                self.state_machine.transition(Signal.REFLECTION_DONE)

            elif current_state == AgentState.REPLANNING:
                # 重新规划后回到 REASONING
                self.state_machine.transition(Signal.REPLAN_READY)

            elif current_state == AgentState.WAITING_CONFIRM:
                # 等待用户确认 - 在当前实现中，我们跳过确认
                self.state_machine.transition(Signal.USER_CONFIRMED)

            else:
                # 其他状态，继续循环
                logger.warning(f"Unexpected state: {current_state.value}")
                break

        # 检查终止状态
        final_state = self.state_machine.current_state
        logger.info(f"=== Agent Run Completed (State: {final_state.value}) ===")

        if final_state == AgentState.SUCCESS:
            # 阶段3：在结束时沉淀经验
            self._store_session_lessons(final_state.value)
            return AgentResponse(
                answer="任务已成功完成",
                token_usage=self.context_manager.get_token_usage(),
                iterations=self.iteration_count
            )
        elif final_state == AgentState.FAILED:
            # 生成失败报告
            stats = self.failure_observer.get_statistics()
            # 阶段3：沉淀经验
            self._store_session_lessons(final_state.value)
            return AgentResponse(
                answer=f"任务执行失败。失败次数: {stats['total_failures']}",
                token_usage=self.context_manager.get_token_usage(),
                iterations=self.iteration_count
            )
        elif final_state == AgentState.TIMEOUT:
            # 阶段3：沉淀经验
            self._store_session_lessons(final_state.value)
            return AgentResponse(
                answer="任务超时，请尝试将任务拆分为更小的子任务。",
                token_usage=self.context_manager.get_token_usage(),
                iterations=self.iteration_count
            )
        else:
            return AgentResponse(
                answer="任务已结束",
                token_usage=self.context_manager.get_token_usage(),
                iterations=self.iteration_count
            )

    def _check_exit_tool(self, tool_calls: list, tool_results: list) -> int | None:
        """检查是否有 exit tool 调用

        Returns:
            exit_code if exit tool was called, None otherwise
        """
        for tool_call, tool_result in zip(tool_calls, tool_results, strict=False):
            if tool_call.tool_name == "exit":
                # 提取 exit_code
                if tool_result.metadata and "exit_context" in tool_result.metadata:
                    return tool_result.metadata["exit_context"].get("exit_code", 0)
                return 0
        return None

    def _get_system_prompt(self) -> str:
        """
        获取 system prompt - 根据是否启用混合执行返回对应的提示词

        Returns:
            str: System prompt
        """
        # 如果启用了混合执行系统，使用优化后的提示词
        if self.execution_router is not None:
            return HYBRID_EXECUTION_SYSTEM_PROMPT
        else:
            # 否则使用默认的 Agent system prompt
            return self.context_manager.get_system_prompt()

    async def _call_llm(self) -> LLMResponse:
        """
        调用 LLM

        Returns:
            LLMResponse: LLM 响应
        """
        # 获取 system prompt（支持混合执行系统）
        system_prompt = self._get_system_prompt()

        # 获取 messages（包含 Plan Recitation）
        messages = self.context_manager.get_messages_for_llm(include_plan_recitation=True)

        # 获取 tool definitions (Claude 不需要在每次调用时传入，但其他模型可能需要)
        # tools = self.context_manager.get_tool_definitions()

        # 调用 LLM
        logger.info(f"Calling LLM with {len(messages)} messages")
        response = await self.llm.complete(
            messages=messages,
            system=system_prompt,
            # tools=tools,  # 暂时不传入，因为我们用自定义格式
        )

        logger.info(f"LLM response received: {len(response.content)} chars")
        return response

    async def _handle_tool_results(self, tool_calls: list, tool_results: list):
        """
        处理工具执行结果

        实现核心规则：
        1. 铁律四: FailureSignal 观察和学习
        2. Keep the Failures: 记录错误到 progress.md
        3. 2-Action Rule: 搜索操作计数
        4. 3-Strike Protocol: 错误计数

        Args:
            tool_calls: 工具调用列表
            tool_results: 工具结果列表
        """
        for tool_call, tool_result in zip(tool_calls, tool_results, strict=False):
            tool_name = tool_call.tool_name

            # =================================================================
            # 铁律四: 创建 FailureSignal 并观察
            # =================================================================
            failure_signal = FailureSignal.from_tool_result(
                tool_name=tool_name,
                success=tool_result.success,
                error=tool_result.error,
                stderr=getattr(tool_result, 'stderr', ''),
                tool_args=tool_call.parameters,
            )

            # 观察失败信号
            observe_result = self.failure_observer.observe(failure_signal)

            # 如果触发 3-Strike，记录日志
            if observe_result.get("trigger_3_strike"):
                logger.warning(
                    f"3-Strike Protocol triggered for {tool_name} "
                    f"(learning: {observe_result.get('learning')})"
                )

            # =================================================================
            # 2-Action Rule: 搜索操作计数
            # =================================================================
            if tool_name in ["web_search", "read_url"]:
                should_remind = self.three_files.record_action(tool_name, {
                    "params": tool_call.parameters,
                    "success": tool_result.success
                })

                if should_remind:
                    logger.warning("2-Action Rule triggered: Remind agent to record findings")
                    reminder = FINDINGS_REMINDER_PROMPT.format(action_count=2)
                    self.context_manager.add_user_message(reminder)

            # =================================================================
            # Keep the Failures: 处理错误
            # =================================================================
            if not tool_result.success:
                logger.error(f"Tool {tool_name} failed: {tool_result.error}")

                # 记录错误到 progress.md (通过 ThreeFilesManager)
                error_info = self.three_files.record_error(
                    error_type=tool_name,
                    error_message=tool_result.error or "Unknown error"
                )

                # 检查是否触发 3-Strike Protocol
                if error_info.get("should_reread_plan") or observe_result.get("trigger_3_strike"):
                    logger.warning(f"3-Strike Protocol triggered for {tool_name}")
                    # 注入错误恢复提示
                    recovery_prompt = ERROR_RECOVERY_PROMPT.format(
                        count=error_info.get("count", 3)
                    )
                    self.context_manager.add_user_message(recovery_prompt)

                    # 同时注入失败学习信息 (铁律四: 智能来自失败)
                    learning = failure_signal.get_learning()
                    if learning:
                        self.context_manager.add_user_message(
                            f"[System Hint] 从失败中学习: {learning}"
                        )
            else:
                # 成功：记录到 progress.md
                self.three_files.update_progress(
                    log_entry=f"✅ Successfully executed {tool_name}",
                    is_error=False
                )

    async def stream(self, user_message: str) -> AsyncGenerator[str, None]:
        """
        流式运行 Agent（用于实时 UI 更新）

        Args:
            user_message: 用户输入

        Yields:
            str: 流式输出块
        """
        # TODO: 实现流式输出
        # 目前先使用 run() 然后返回完整结果
        response = await self.run(user_message)
        yield response.answer

    def get_context_summary(self) -> dict[str, Any]:
        """
        获取当前 context 摘要（用于调试）

        包含状态机和失败观察器信息 (铁律一 + 铁律四)

        Returns:
            Dict: Context 摘要
        """
        return {
            "session_id": self.session_id,
            "workspace_id": self.workspace_id,
            "message_count": self.context_manager.get_message_count(),
            "iteration_count": self.iteration_count,
            "token_usage": self.context_manager.get_token_usage(),
            # 铁律一: 状态机信息
            "state_machine": {
                "current_state": self.state_machine.current_state.value,
                "is_terminal": self.state_machine.is_terminal(),
                "history_length": len(self.state_machine.history.entries),
            },
            # 铁律四: 失败观察器统计
            "failure_stats": self.failure_observer.get_statistics(),
            # 工作记忆
            "working_memory": {
                "task_plan": self.three_files.read_task_plan(),
                "file_paths": self.three_files.get_file_paths()
            },
            # 最后退出码
            "last_exit_code": self._last_exit_code,
        }

    def _on_failure_signal(self, signal: FailureSignal) -> None:
        """失败回调：记录到模式库，并尝试直接给出已知修复方案"""
        try:
            # 记录到知识库
            self.pattern_kb.record(signal)
            # 如果已存在成功修复方案，直接注入提示
            solution = self.pattern_kb.get_solution(signal)
            if solution:
                self.context_manager.add_user_message(
                    f"[KB] 检测到已知失败模式，建议直接应用方案：{solution}"
                )
        except Exception as e:
            logger.error(f"Failure callback error: {e}")

    def _store_session_lessons(self, final_state: str) -> None:
        """将本次会话的经验沉淀到分布式记忆"""
        try:
            stats = self.failure_observer.get_statistics()
            total = stats.get("total_signals", 0)
            failures = stats.get("total_failures", 0)
            lesson_summary = (
                f"本次会话结束状态: {final_state}. 操作总数 {total}, 失败 {failures}.\n"
                f"最常见错误: {max(stats.get('by_type',{}), key=stats.get('by_type',{}).get) if stats.get('by_type') else 'N/A'}."
            )
            self.distributed_memory.store_lessons([
                Lesson(
                    title="Session Summary & Lessons",
                    summary=lesson_summary,
                    tags=["lessons", "robustness"],
                    created_at=datetime.utcnow().isoformat() + "Z",  # type: ignore
                )
            ])
        except Exception as e:
            logger.error(f"Store lessons failed: {e}")

    def _maybe_compress_context(self, current_tokens: int, force_aggressive: bool = False) -> None:
        """在接近阈值时压缩上下文

        Args:
            current_tokens: 当前使用的 token 数
            force_aggressive: 是否强制激进压缩
        """
        try:
            should, strategy = self.context_compressor.should_compress(current_tokens)
            if force_aggressive:
                should, strategy = True, "aggressive"
            if not should:
                return

            # 序列化消息为 Dict 以便压缩
            raw_messages: list[dict[str, Any]] = []
            for m in self.context_manager.messages:
                raw_messages.append({
                    "role": m.role,
                    "content": m.content,
                    "metadata": m.metadata or {},
                })
            compressed_messages, result = self.context_compressor.compress(
                raw_messages,
                current_tokens=current_tokens,
                strategy=strategy,
            )

            # 反序列化写回 ContextManager
            self.context_manager.messages = [
                CtxMessage(role=msg.get("role","user"), content=msg.get("content",""), metadata=msg.get("metadata"))
                for msg in compressed_messages
            ]

            # 在 progress 中记录
            self.three_files.update_progress(
                log_entry=(
                    f"🪶 Context compressed via {result.strategy_used}: "
                    f"{result.tokens_before} → {result.tokens_after} (saved {result.tokens_saved})"
                ),
                is_error=False,
            )
            logger.info(
                f"Context compressed: {result.tokens_before}->{result.tokens_after} tokens"
            )
        except Exception as e:
            logger.error(f"Context compression failed: {e}")

    def reset(self):
        """
        重置 Agent 状态（用于新对话）

        重置包括状态机和失败观察器
        """
        # 清理 Context
        self.context_manager.clear()
        self.tool_registry.reset_allowed_tools()
        self._current_skill_match = None
        self.iteration_count = 0

        # 铁律一: 重置状态机
        self.state_machine.reset()

        # 铁律四: 重置失败观察器
        self.failure_observer.clear()
        self._last_exit_code = None

        logger.info("Agent state reset (including state machine and failure observer)")

    # =========================================================================
    # Skill 系统集成
    # =========================================================================

    async def _match_and_inject_skill(self, user_message: str) -> None:
        """执行混合路由决策和执行

        Phase 2 改进版工作流程：
        1. 使用 ExecutionRouter 决定执行路径（Skill / MCP / LLM）
        2. 根据路径选择执行方式
        3. 记录执行到 UnifiedExecutionContext
        4. 注入结果到 Context

        三路分支：
        - Path A (Skill): 预制脚本执行（< 100ms）
        - Path B (MCP): 动态代码生成执行（< 5s）
        - Path C (LLM): 纯推理（无执行）

        Args:
            user_message: 用户消息
        """
        if not self.enable_skills or not self.execution_router:
            return

        try:
            # Step 1: 路由决策
            routing_decision = await self.execution_router.route(user_message)
            logger.info(
                f"Execution path selected: {routing_decision.path.value} "
                f"(confidence={routing_decision.confidence:.2f}, reason={routing_decision.reason})"
            )

            # Step 2: 根据路由路径执行
            execution_result = None

            if routing_decision.path == ExecutionPath.SKILL:
                # Path A: Skill 执行
                execution_result = await self._execute_skill_path(user_message)

            elif routing_decision.path == ExecutionPath.MCP_CODE:
                # Path B: MCP 代码执行
                execution_result = await self._execute_mcp_path(user_message)

            else:
                # Path C: LLM 推理（无需执行）
                logger.info("Routing to LLM reasoning path (pure inference)")

            # Step 3: 记录到统一上下文
            if execution_result:
                self.unified_context.set_var("last_execution_result", execution_result)
                logger.info(
                    f"Execution result recorded in unified context: "
                    f"{execution_result.get('status', 'unknown')}"
                )

            # Step 4: 注入到 Agent Context
            if execution_result and execution_result.get("status") == "success":
                self._inject_execution_result(execution_result, routing_decision.path)

        except Exception as e:
            logger.error(f"Hybrid execution failed: {e}")
            self._clear_skill_state()

    async def _execute_skill_path(self, user_message: str) -> dict[str, Any] | None:
        """执行 Skill 路径

        Args:
            user_message: 用户消息

        Returns:
            执行结果或 None
        """
        if not self.skill_matcher:
            return None

        try:
            # 匹配 Skill
            match = await self.skill_matcher.match(user_message)

            if match and match.is_confident():
                self._current_skill_match = match
                logger.info(
                    f"Skill matched: {match.skill_id} "
                    f"(score={match.score:.2f}, reason={match.reason})"
                )

                # 记录执行开始
                exec_record = self.unified_context.record_execution(
                    execution_type=ExecutionType.SKILL,
                    user_message=user_message,
                    status=ExecutionStatus.RUNNING,
                )

                try:
                    # 加载 L2 指令
                    l2_instructions = await self.skill_loader.load_l2(match.skill_id)

                    # 获取 Skill 元数据
                    skill_meta = match.metadata
                    if not skill_meta:
                        skill_meta = self.skill_registry.get(match.skill_id)

                    if skill_meta and skill_meta.allowed_tools:
                        self.tool_registry.set_allowed_tools(skill_meta.allowed_tools)
                        logger.info("Action Space Pruning: tools limited")

                    # 执行 L3 脚本
                    skill_result = await self._try_execute_skill(
                        match.skill_id,
                        user_message,
                    )

                    # 构建结果
                    if skill_result and skill_result.get("status") == "success":
                        result_summary = self._format_skill_result(skill_result)
                        l2_instructions = (
                            f"## Skill 执行结果\n{result_summary}\n\n"
                            f"## 后续指令\n{l2_instructions}"
                        )

                        # 更新执行记录
                        self.unified_context.update_execution_record(
                            execution_id=exec_record.execution_id,
                            status=ExecutionStatus.SUCCESS,
                            result=skill_result,
                        )

                        logger.info(f"Skill {match.skill_id} executed successfully")
                        return {
                            "status": "success",
                            "path": ExecutionPath.SKILL.value,
                            "skill_id": match.skill_id,
                            "result": skill_result,
                            "instructions": l2_instructions,
                        }
                    else:
                        # 执行失败，尝试降级
                        error_msg = skill_result.get("error", "Unknown error") if skill_result else "Skill execution failed"
                        self.unified_context.update_execution_record(
                            execution_id=exec_record.execution_id,
                            status=ExecutionStatus.FAILED,
                            error=error_msg,
                        )
                        logger.warning(f"Skill execution failed: {error_msg}, attempting fallback")

                        # 注入仅指令版本
                        if skill_meta:
                            self.context_manager.inject_skill(
                                skill_id=match.skill_id,
                                display_name=skill_meta.display_name,
                                l2_instructions=l2_instructions,
                                allowed_tools=skill_meta.allowed_tools,
                            )
                        return None

                except Exception as e:
                    self.unified_context.update_execution_record(
                        execution_id=exec_record.execution_id,
                        status=ExecutionStatus.FAILED,
                        error=str(e),
                    )
                    logger.error(f"Skill execution error: {e}")
                    return None
            else:
                logger.debug("No confident Skill match")
                return None

        except Exception as e:
            logger.error(f"Skill path execution failed: {e}")
            return None

    async def _execute_mcp_path(self, user_message: str) -> dict[str, Any] | None:
        """执行 MCP 代码执行路径

        Args:
            user_message: 用户消息

        Returns:
            执行结果或 None
        """
        try:
            logger.info("Entering MCP code execution path")

            # 记录执行开始
            exec_record = self.unified_context.record_execution(
                execution_type=ExecutionType.MCP_CODE,
                user_message=user_message,
                status=ExecutionStatus.RUNNING,
            )

            # Step 1: LLM 生成代码
            logger.info("Requesting LLM to generate code...")

            # 这里应该调用 LLM，但现在先标记为待实现
            # generated_code = await self.llm.generate(code_generation_prompt)
            logger.warning("LLM code generation not yet integrated in Phase 3")

            self.unified_context.update_execution_record(
                execution_id=exec_record.execution_id,
                status=ExecutionStatus.FAILED,
                error="MCP code generation not yet implemented",
            )
            return None

        except Exception as e:
            logger.error(f"MCP path execution failed: {e}")
            return None

    def _inject_execution_result(
        self, execution_result: dict[str, Any], path: ExecutionPath
    ) -> None:
        """将执行结果注入到 Agent Context

        Args:
            execution_result: 执行结果
            path: 执行路径
        """
        try:
            if path == ExecutionPath.SKILL and "instructions" in execution_result:
                # Skill 结果：注入 L2 指令
                skill_id = execution_result.get("skill_id")
                if self.skill_registry and skill_id:
                    skill_meta = self.skill_registry.get(skill_id)
                    if skill_meta:
                        self.context_manager.inject_skill(
                            skill_id=skill_id,
                            display_name=skill_meta.display_name,
                            l2_instructions=execution_result["instructions"],
                            allowed_tools=skill_meta.allowed_tools,
                        )
                        logger.info(f"Skill result injected to context: {skill_id}")

            # 记录到 progress.md
            self.three_files.update_progress(
                log_entry=f"✅ Execution completed via {path.value}",
                is_error=False
            )

        except Exception as e:
            logger.error(f"Failed to inject execution result: {e}")

    def _clear_skill_state(self) -> None:
        """清除 Skill 状态"""
        self._current_skill_match = None
        self.context_manager.clear_skill()
        self.tool_registry.reset_allowed_tools()

    def get_current_skill(self) -> SkillMatch | None:
        """获取当前激活的 Skill

        Returns:
            当前的 SkillMatch，或 None
        """
        return self._current_skill_match

    async def _try_execute_skill(
        self,
        skill_id: str,
        user_message: str,
    ) -> dict[str, Any] | None:
        """尝试执行 Skill 的 L3 脚本

        Args:
            skill_id: Skill ID
            user_message: 用户消息

        Returns:
            执行结果或 None（如果执行器不可用）
        """
        if not self.skill_executor:
            logger.debug("Skill executor not available, skipping execution")
            return None

        try:
            # 检查 Skill 是否可执行
            if not self.skill_executor.can_execute(skill_id):
                logger.debug(f"Skill {skill_id} is not executable (no execute.py)")
                return None

            # 执行 Skill
            result = await self.skill_executor.execute(
                skill_id=skill_id,
                query=user_message,
                context={
                    "user_id": "unknown",  # TODO: 从 session 提取
                    "session_id": self.session_id,
                    "workspace_id": self.workspace_id,
                },
            )

            return result

        except Exception as e:
            logger.error(f"Error executing skill {skill_id}: {e}", exc_info=True)
            return None

    def _format_skill_result(self, result: dict[str, Any]) -> str:
        """格式化 Skill 执行结果为 Markdown

        Args:
            result: 执行结果

        Returns:
            Markdown 格式的结果
        """
        status = result.get("status", "unknown")
        data = result.get("data")
        error = result.get("error")
        tokens_used = result.get("tokens_used", 0)

        parts = []

        if status == "success" and data:
            parts.append("**执行成功**")
            parts.append("")

            # 需要根据执行结果的具体类型首倶体提供不同格式
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (str, int, float, bool)):
                        parts.append(f"- **{key}**: {value}")
                    elif isinstance(value, list):
                        parts.append(f"- **{key}**: ({len(value)} items)")
            elif isinstance(data, str):
                # 提取简介（最多 500 个字符）
                parts.append(data[:500])
                if len(data) > 500:
                    parts.append("...")
            else:
                parts.append(str(data)[:500])

        elif status == "timeout":
            parts.append("**执行超时**")
            parts.append("Skill 执行超时，平地执行后续Prompt 准备手动执行。")

        elif status == "failed" and error:
            parts.append("**执行失败**")
            parts.append(f"{error}")

        # 添加 Token 統計
        if tokens_used > 0:
            parts.append("")
            parts.append(f"*Token 使用：{tokens_used}*")

        return "\n".join(parts)

    # =========================================================================
    # Planning-Based Execution (统一架构)
    # =========================================================================

    async def run_stream_with_planning(
        self,
        user_message: str,
        enable_parallel: bool = True
    ) -> AsyncGenerator[SSEEvent, None]:
        """
        带 Planning 的流式执行（统一架构）

        核心设计：
        - 流程控制权归代码（TaskScheduler）
        - 内容生成权归模型（LLM）
        - 每步可验证、可重试、可恢复

        Args:
            user_message: 用户目标
            enable_parallel: 是否启用并行执行

        Yields:
            SSEEvent: SSE 事件流
        """
        logger.info("=== Planning-Based Agent Run Started ===")
        logger.info(f"Goal: {user_message}")

        # 重置状态
        self.scheduler = TaskScheduler()
        self._current_plan = None
        self.iteration_count = 0

        try:
            # Phase 1: Planning
            yield SSEEvent(
                type=SSEEventType.STATUS,
                data={"phase": "planning", "message": "正在分析任务并制定计划..."}
            )

            # 生成 Plan
            self._current_plan = await self.planner.plan(user_message)
            self.scheduler.load_plan(self._current_plan)

            # 推送 Plan 创建事件
            yield self.plan_event_emitter.plan_created(self._current_plan)

            logger.info(
                f"Plan created: {self._current_plan.id} "
                f"with {len(self._current_plan.tasks)} tasks"
            )

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

                # 获取可执行任务
                ready_tasks = self.scheduler.get_ready_tasks()

                if not ready_tasks:
                    if self.scheduler.is_blocked():
                        logger.error("Plan is blocked")
                        yield SSEEvent(
                            type=SSEEventType.ERROR,
                            data={"message": "任务执行被阻塞，可能需要人工介入"}
                        )
                        break
                    continue

                # 并行执行多个独立任务
                if enable_parallel and len(ready_tasks) > 1:
                    # 并行执行
                    async for event in self._execute_tasks_parallel(ready_tasks):
                        yield event
                else:
                    # 串行执行第一个
                    async for event in self._execute_single_task(ready_tasks[0]):
                        yield event

                # 发送进度更新
                yield self.plan_event_emitter.progress_update(self._current_plan)

            # Phase 3: Completion
            if self._current_plan.is_complete():
                yield SSEEvent(
                    type=SSEEventType.DONE,
                    data={
                        "status": "success",
                        "message": "所有任务执行完成",
                        "iterations": self.iteration_count,
                        "progress": self._current_plan.get_progress()
                    }
                )
            else:
                yield SSEEvent(
                    type=SSEEventType.DONE,
                    data={
                        "status": "incomplete",
                        "message": "任务未完全完成",
                        "iterations": self.iteration_count,
                        "progress": self._current_plan.get_progress()
                    }
                )

        except Exception as e:
            logger.error(f"Planning agent error: {e}", exc_info=True)
            yield SSEEvent(
                type=SSEEventType.ERROR,
                data={"message": str(e), "type": e.__class__.__name__}
            )

    async def _execute_tasks_parallel(
        self,
        tasks: list[Task]
    ) -> AsyncGenerator[SSEEvent, None]:
        """
        并行执行多个任务

        Args:
            tasks: 可并行执行的任务列表

        Yields:
            SSEEvent: 任务执行事件
        """
        logger.info(f"Executing {len(tasks)} tasks in parallel")

        # 标记所有任务开始
        for task in tasks:
            self.scheduler.start_task(task.id)
            yield self.plan_event_emitter.task_start(task)

        # 并行执行
        results = await asyncio.gather(
            *[self._execute_task_core(task) for task in tasks],
            return_exceptions=True
        )

        # 处理结果
        for task, result in zip(tasks, results, strict=False):
            if isinstance(result, Exception):
                # 任务失败
                error_msg = str(result)
                failed_task, decision = self.scheduler.fail_task(task.id, error_msg)
                yield self.plan_event_emitter.task_failed(task)

                yield SSEEvent(
                    type=SSEEventType.ERROR,
                    data={
                        "message": f"任务 '{task.title}' 执行失败: {error_msg}",
                        "taskId": task.id,
                        "decision": decision.value
                    }
                )

                # 处理重规划
                if decision == ReplanDecision.REPLAN:
                    async for event in self._handle_replan(task, error_msg):
                        yield event
            else:
                # 任务成功
                output = result if isinstance(result, str) else str(result)
                self.scheduler.complete_task(task.id, output[:500])
                yield self.plan_event_emitter.task_complete(task)

                yield SSEEvent(
                    type=SSEEventType.CONTENT,
                    data={"content": f"\n✅ {task.title} 完成\n"}
                )

    async def _execute_single_task(
        self,
        task: Task
    ) -> AsyncGenerator[SSEEvent, None]:
        """
        执行单个任务

        Args:
            task: 要执行的任务

        Yields:
            SSEEvent: 任务执行事件
        """
        logger.info(f"Executing task: {task.title} ({task.id})")

        # 标记任务开始
        self.scheduler.start_task(task.id)
        yield self.plan_event_emitter.task_start(task)

        try:
            # 执行任务
            yield SSEEvent(
                type=SSEEventType.THINKING,
                data={"content": f"正在执行: {task.title}...\n"}
            )

            output = await self._execute_task_core(task)

            # 标记任务完成
            self.scheduler.complete_task(task.id, output[:500] if output else "")
            yield self.plan_event_emitter.task_complete(task)

            yield SSEEvent(
                type=SSEEventType.CONTENT,
                data={"content": f"\n✅ {task.title} 完成\n"}
            )

        except Exception as e:
            logger.error(f"Task execution failed: {e}")

            # 标记任务失败
            failed_task, decision = self.scheduler.fail_task(task.id, str(e))
            yield self.plan_event_emitter.task_failed(task)

            yield SSEEvent(
                type=SSEEventType.ERROR,
                data={
                    "message": f"任务 '{task.title}' 执行失败: {e}",
                    "taskId": task.id,
                    "decision": decision.value
                }
            )

            # 处理重规划
            if decision == ReplanDecision.REPLAN:
                async for event in self._handle_replan(task, str(e)):
                    yield event

    async def _execute_task_core(self, task: Task) -> str:
        """
        任务执行核心逻辑

        这是"LLM 只负责如何完成这个原子任务"的体现

        Args:
            task: 要执行的任务

        Returns:
            str: 任务执行输出
        """
        # 生成 Plan Recitation
        assert self._current_plan is not None, "Plan must be initialized"
        recitation = self.plan_reciter.generate(self._current_plan, self.scheduler)

        # 构建任务执行 Prompt
        prompt = f"""Please complete the following task:

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

        system_prompt = f"""You are an AI assistant executing a specific task within a larger plan.

Your current task is: {task.title}

Rules:
1. Focus ONLY on completing this specific task
2. Do NOT try to do other tasks or plan ahead
3. Use the suggested tools if available
4. Complete the task according to the acceptance criteria
5. Be concise and efficient

If you cannot complete the task, explain why clearly."""

        # 调用 LLM
        response = await self.llm.complete(
            messages=[LLMMessage(role="user", content=prompt)],
            system=system_prompt,
        )

        return response.content

    async def _handle_replan(
        self,
        failed_task: Task,
        error: str
    ) -> AsyncGenerator[SSEEvent, None]:
        """
        处理重规划

        Args:
            failed_task: 失败的任务
            error: 错误信息

        Yields:
            SSEEvent: 重规划相关事件
        """
        yield SSEEvent(
            type=SSEEventType.THINKING,
            data={"content": "正在重新规划...\n"}
        )

        assert self._current_plan is not None, "Plan must exist to replan"

        # 调用 AtomicPlanner 重规划
        new_plan = await self.planner.replan(
            self._current_plan,
            failed_task,
            error
        )

        # 更新调度器
        self.scheduler.replace_plan(new_plan)
        self._current_plan = new_plan

        # 推送重规划事件
        yield self.plan_event_emitter.plan_revised(new_plan, error)

        yield SSEEvent(
            type=SSEEventType.CONTENT,
            data={"content": f"\n🔄 计划已重新调整，新版本: v{new_plan.version}\n"}
        )

    def get_current_plan(self) -> Plan | None:
        """获取当前 Plan"""
        return self._current_plan

    def get_plan_progress(self) -> dict[str, Any]:
        """获取当前进度"""
        if self._current_plan:
            return self._current_plan.get_progress()
        return {"total": 0, "completed": 0, "percentage": 0}
