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
    
    async def _call_llm(self) -> LLMResponse:
        """
        调用 LLM
        
        Returns:
            LLMResponse: LLM 响应
        """
        # 获取 system prompt
        system_prompt = self.context_manager.get_system_prompt()
        
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
        """匹配 Skill 并尝试自动执行
        
        工作流程：
        1. 匹配用户消息到最相关的 Skill
        2. 尝试执行 Skill 的 L3 脚本（如果存在）
        3. 如果执行成功，注入执行结果到 Context
        4. 如果执行失败或 Skill 无脚本，回退到仅注入 L2 指令
        
        Args:
            user_message: 用户消息
        """
        if not self.enable_skills or not self.skill_matcher:
            return
        
        try:
            # 匹配 Skill
            match = await self.skill_matcher.match(user_message)
            
            if match and match.is_confident():
                self._current_skill_match = match
                logger.info(
                    f"Skill matched: {match.skill_id} "
                    f"(score={match.score:.2f}, reason={match.reason})"
                )
                
                # 加载 L2 指令
                l2_instructions = await self.skill_loader.load_l2(match.skill_id)
                
                # 获取 Skill 元数据
                skill_meta = match.metadata
                if not skill_meta:
                    skill_meta = self.skill_registry.get(match.skill_id)
                
                if skill_meta:
                    # Action Space Pruning: 限制可用工具
                    if skill_meta.allowed_tools:
                        self.tool_registry.set_allowed_tools(skill_meta.allowed_tools)
                        logger.info(
                            f"Action Space Pruning: tools limited to {skill_meta.allowed_tools}"
                        )
                    
                    # 尝试执行 L3 脚本（如果存在）
                    skill_execution_result = await self._try_execute_skill(
                        match.skill_id,
                        user_message,
                    )
                    
                    # 构建注入内容：执行结果 + L2 指令
                    if skill_execution_result and skill_execution_result.get("status") == "success":
                        # 执行成功，注入结果 + 指令
                        skill_result_summary = self._format_skill_result(
                            skill_execution_result
                        )
                        l2_instructions = (
                            f"## Skill 执行结果\n{skill_result_summary}\n\n"
                            f"## 后续指令\n{l2_instructions}"
                        )
                        logger.info(
                            f"Skill {match.skill_id} executed successfully, "
                            f"result injected into context"
                        )
                    else:
                        # 执行失败或无脚本，仅注入指令（降级策略）
                        if skill_execution_result:
                            error_msg = skill_execution_result.get(
                                "error",
                                "Unknown execution error"
                            )
                            logger.warning(
                                f"Skill {match.skill_id} execution failed, "
                                f"falling back to instruction injection: {error_msg}"
                            )
                    
                    # 注入 Skill 指令到 Context
                    self.context_manager.inject_skill(
                        skill_id=match.skill_id,
                        display_name=skill_meta.display_name,
                        l2_instructions=l2_instructions,
                        allowed_tools=skill_meta.allowed_tools,
                    )
            else:
                # 没有匹配到 Skill，清除之前的 Skill 状态
                self._clear_skill_state()
                
        except Exception as e:
            logger.error(f"Skill matching failed: {e}")
            self._clear_skill_state()
    
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
