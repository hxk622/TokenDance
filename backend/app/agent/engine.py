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

from typing import Optional, Dict, List, Any, AsyncGenerator
from dataclasses import dataclass, field
import asyncio

from app.agent.context_manager import ContextManager
from app.agent.executor import ToolCallExecutor
from app.agent.tools.registry import ToolRegistry
from app.agent.working_memory.three_files import ThreeFilesManager
from app.agent.llm.base import BaseLLM, LLMResponse
from app.agent.prompts import ERROR_RECOVERY_PROMPT, FINDINGS_REMINDER_PROMPT
from app.agent.hybrid_execution_prompts import (
    HYBRID_EXECUTION_SYSTEM_PROMPT,
    MCP_CODE_GENERATION_PROMPT,
    EXECUTION_PATH_SELECTION_PROMPT,
)
from app.filesystem import AgentFileSystem
from app.core.logging import get_logger

# 状态机和失败信号系统 (铁律一 + 铁律四)
from app.agent.state import (
    AgentState,
    Signal,
    StateMachine,
    StateHistory,
    InvalidStateTransition,
)
from app.agent.failure import (
    FailureSignal,
    FailureObserver,
    FailureSummary,
    ExitCode,
)

# Skill System imports
from app.skills import (
    get_skill_registry,
    get_skill_matcher,
    SkillLoader,
    SkillMatch,
    get_skill_executor,
)

# Phase 2: Hybrid Execution imports
from app.routing.router import (
    ExecutionRouter,
    ExecutionPath,
    get_execution_router,
    reset_execution_router,
)
from app.context.unified_context import (
    UnifiedExecutionContext,
    ExecutionType,
    ExecutionStatus,
    get_unified_context,
)
from app.mcp.executor import (
    MCPCodeExecutor,
    ExecutionRequest,
    ExecutionLanguage,
    get_mcp_executor,
)

logger = get_logger(__name__)


@dataclass
class AgentResponse:
    """Agent 响应"""
    answer: str
    reasoning: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None
    token_usage: Optional[Dict[str, int]] = None
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
        max_iterations: int = 20,
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
        
        # 状态
        self.iteration_count = 0
        self._current_skill_match: Optional[SkillMatch] = None
        self._last_exit_code: Optional[int] = None  # 铁律四: 记录最后退出码
        
        logger.info(
            f"Agent Engine initialized for session {session_id} "
            f"(skills={enable_skills}, state_machine=enabled)"
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
        logger.info(f"=== Agent Run Started (State Machine) ===")
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
        last_reasoning: Optional[str] = None
        
        # 状态机主循环
        while not self.state_machine.is_terminal():
            self.iteration_count += 1
            logger.info(f"--- Iteration {self.iteration_count} (State: {self.state_machine.current_state.value}) ---")
            
            # 检查迭代次数限制
            if self.iteration_count > self.max_iterations:
                logger.warning(f"Max iterations ({self.max_iterations}) reached")
                self.state_machine.transition(Signal.MAX_ITERATIONS)
                break
            
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
                    self.context_manager.update_token_usage(
                        input_tokens=llm_response.usage.get("input_tokens", 0),
                        output_tokens=llm_response.usage.get("output_tokens", 0)
                    )
                
                # 提取推理过程
                last_reasoning = self.executor.extract_reasoning(llm_response.content)
                if last_reasoning:
                    logger.info(f"Reasoning: {last_reasoning[:200]}...")
                
                # 决策：检查 LLM 响应内容
                if self.executor.has_final_answer(llm_response.content):
                    # 有最终答案 → 发送 TASK_COMPLETE 信号
                    answer = self.executor.extract_answer(llm_response.content)
                    logger.info(f"Final answer received")
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
                            for tc, tr in zip(tool_calls, tool_results)
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
                # 反怕状态：读取失败摘要，准备重新规划
                failure_summary = self.failure_observer.get_failure_summary_for_context()
                if failure_summary:
                    # 注入失败摘要到 Context (Plan Recitation)
                    self.context_manager.add_user_message(
                        f"[System] 请根据以下失败记录调整策略:\n{failure_summary}"
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
            return AgentResponse(
                answer="任务已成功完成",
                token_usage=self.context_manager.get_token_usage(),
                iterations=self.iteration_count
            )
        elif final_state == AgentState.FAILED:
            # 生成失败报告
            stats = self.failure_observer.get_statistics()
            return AgentResponse(
                answer=f"任务执行失败。失败次数: {stats['total_failures']}",
                token_usage=self.context_manager.get_token_usage(),
                iterations=self.iteration_count
            )
        elif final_state == AgentState.TIMEOUT:
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
    
    def _check_exit_tool(self, tool_calls: List, tool_results: List) -> Optional[int]:
        """检查是否有 exit tool 调用
        
        Returns:
            exit_code if exit tool was called, None otherwise
        """
        for tool_call, tool_result in zip(tool_calls, tool_results):
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
    
    async def _handle_tool_results(self, tool_calls: List, tool_results: List):
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
        for tool_call, tool_result in zip(tool_calls, tool_results):
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
    
    def get_context_summary(self) -> Dict[str, Any]:
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
            routing_decision = self.execution_router.route(user_message)
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
    
    async def _execute_skill_path(self, user_message: str) -> Optional[Dict[str, Any]]:
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
                        logger.info(f"Action Space Pruning: tools limited")
                    
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
    
    async def _execute_mcp_path(self, user_message: str) -> Optional[Dict[str, Any]]:
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
            code_generation_prompt = (
                f"用户要求：{user_message}\n\n"
                f"请生成 Python 代码来完成上述任务。"
                f"代码必须符合以下要求：\n"
                f"1. 不能导入 os, sys, subprocess 等系统库\n"
                f"2. 不能使用 eval, exec 等动态执行\n"
                f"3. 必须有完善的错误处理\n"
                f"4. 输出结果用 print() 打印\n\n"
                f"请在```python和```之间提供代码。"
            )
            
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
        self, execution_result: Dict[str, Any], path: ExecutionPath
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
    
    def get_current_skill(self) -> Optional[SkillMatch]:
        """获取当前激活的 Skill
        
        Returns:
            当前的 SkillMatch，或 None
        """
        return self._current_skill_match
    
    async def _try_execute_skill(
        self,
        skill_id: str,
        user_message: str,
    ) -> Optional[Dict[str, Any]]:
        """尝试执行 Skill 的 L3 脚本
        
        Args:
            skill_id: Skill ID
            user_message: 用户消息
            
        Returns:
            执行结果或 None（如果执行器不可用）
        """
        if not self.skill_executor:
            logger.debug(f"Skill executor not available, skipping execution")
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
    
    def _format_skill_result(self, result: Dict[str, Any]) -> str:
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
