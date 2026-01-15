"""
Agent Engine - 核心执行循环

实现 Agent 的主循环逻辑：
1. 接收用户输入
2. LLM 推理
3. 解析工具调用
4. 执行工具
5. 更新记忆
6. 返回结果
"""

from typing import Optional, Dict, List, Any, AsyncGenerator
from dataclasses import dataclass
import asyncio

from app.agent.context_manager import ContextManager
from app.agent.executor import ToolCallExecutor
from app.agent.tools.registry import ToolRegistry
from app.agent.working_memory.three_files import ThreeFilesManager
from app.agent.llm.base import BaseLLM, LLMResponse
from app.agent.prompts import ERROR_RECOVERY_PROMPT, FINDINGS_REMINDER_PROMPT
from app.filesystem import AgentFileSystem
from app.core.logging import get_logger

# Skill System imports
from app.skills import (
    get_skill_registry,
    get_skill_matcher,
    SkillLoader,
    SkillMatch,
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
    Agent 核心引擎
    
    核心设计原则：
    1. **Append-Only Context**: 消息只追加，不修改
    2. **Plan Recitation**: 每轮末尾追加 TODO 清单
    3. **Keep the Failures**: 保留错误记录
    4. **2-Action Rule**: 每2次搜索操作后记录 findings
    5. **3-Strike Protocol**: 同类错误3次触发重读计划
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
        # Note: register_builtin_tools 需要在外部调用，或者在这里单独处理
        
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
        
        # 初始化 Skill 系统
        self.skill_registry = None
        self.skill_matcher = None
        self.skill_loader = None
        
        if enable_skills:
            self._init_skill_system()
        
        # 状态
        self.iteration_count = 0
        self._current_skill_match: Optional[SkillMatch] = None
        
        logger.info(f"Agent Engine initialized for session {session_id} (skills={enable_skills})")
    
    def _init_skill_system(self) -> None:
        """初始化 Skill 系统组件"""
        try:
            # 获取 Skill 注册表（全局单例）
            self.skill_registry = get_skill_registry()
            
            # 创建 Skill 匹配器（全局单例）
            self.skill_matcher = get_skill_matcher(self.skill_registry)
            
            # 创建 Skill 加载器
            self.skill_loader = SkillLoader(self.skill_registry)
            
            logger.info(
                f"Skill system initialized: {len(self.skill_registry)} skills available"
            )
        except Exception as e:
            logger.error(f"Failed to initialize skill system: {e}")
            self.enable_skills = False
    
    async def run(self, user_message: str) -> AgentResponse:
        """
        运行 Agent 主循环
        
        Args:
            user_message: 用户输入
            
        Returns:
            AgentResponse: Agent 响应
        """
        logger.info(f"=== Agent Run Started ===")
        logger.info(f"User message: {user_message}")
        
        # Skill 匹配和注入
        await self._match_and_inject_skill(user_message)
        
        # 添加用户消息到 context
        self.context_manager.add_user_message(user_message)
        
        # 重置迭代计数
        self.iteration_count = 0
        
        # 主循环
        while self.iteration_count < self.max_iterations:
            self.iteration_count += 1
            logger.info(f"--- Iteration {self.iteration_count} ---")
            
            # 获取 LLM 响应
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
            reasoning = self.executor.extract_reasoning(llm_response.content)
            if reasoning:
                logger.info(f"Reasoning: {reasoning[:200]}...")
            
            # 检查是否包含最终答案
            if self.executor.has_final_answer(llm_response.content):
                answer = self.executor.extract_answer(llm_response.content)
                logger.info(f"Final answer received: {answer[:200]}...")
                
                return AgentResponse(
                    answer=answer or llm_response.content,
                    reasoning=reasoning,
                    token_usage=self.context_manager.get_token_usage(),
                    iterations=self.iteration_count
                )
            
            # 检查是否包含工具调用
            if self.executor.has_tool_calls(llm_response.content):
                # 解析工具调用
                tool_calls = self.executor.parse_tool_calls(llm_response.content)
                logger.info(f"Parsed {len(tool_calls)} tool calls")
                
                # 执行工具
                tool_results = await self.executor.execute_all(tool_calls)
                
                # 处理工具结果
                await self._handle_tool_results(tool_calls, tool_results)
                
                # 格式化并添加工具结果到 context
                tool_results_text = self.executor.format_tool_results(tool_results)
                self.context_manager.add_tool_result_message(tool_results_text)
                
                # 继续下一轮迭代
                continue
            
            # 如果既没有答案也没有工具调用，直接返回内容
            logger.warning("Response has neither answer nor tool calls, returning content")
            return AgentResponse(
                answer=llm_response.content,
                reasoning=reasoning,
                token_usage=self.context_manager.get_token_usage(),
                iterations=self.iteration_count
            )
        
        # 达到最大迭代次数
        logger.warning(f"Reached max iterations ({self.max_iterations})")
        return AgentResponse(
            answer="I apologize, but I've reached the maximum number of reasoning steps. Please try breaking down your request into smaller tasks.",
            token_usage=self.context_manager.get_token_usage(),
            iterations=self.iteration_count
        )
    
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
        1. 记录错误到 progress.md
        2. 2-Action Rule: 搜索操作计数
        3. 3-Strike Protocol: 错误计数
        
        Args:
            tool_calls: 工具调用列表
            tool_results: 工具结果列表
        """
        for tool_call, tool_result in zip(tool_calls, tool_results):
            tool_name = tool_call.tool_name
            
            # 记录动作（2-Action Rule）
            if tool_name in ["web_search", "read_url"]:
                should_remind = self.three_files.record_action(tool_name, {
                    "params": tool_call.parameters,
                    "success": tool_result.success
                })
                
                if should_remind:
                    # 触发 2-Action Rule 提醒
                    logger.warning("2-Action Rule triggered: Remind agent to record findings")
                    # 注入提醒消息
                    reminder = FINDINGS_REMINDER_PROMPT.format(action_count=2)
                    self.context_manager.add_user_message(reminder)
            
            # 处理错误
            if not tool_result.success:
                logger.error(f"Tool {tool_name} failed: {tool_result.error}")
                
                # 记录错误到 progress.md
                error_info = self.three_files.record_error(
                    error_type=tool_name,
                    error_message=tool_result.error or "Unknown error"
                )
                
                # 检查是否触发 3-Strike Protocol
                if error_info.get("should_reread_plan"):
                    logger.warning(f"3-Strike Protocol triggered for {tool_name}")
                    # 注入错误恢复提示
                    recovery_prompt = ERROR_RECOVERY_PROMPT.format(
                        count=error_info["count"]
                    )
                    self.context_manager.add_user_message(recovery_prompt)
            else:
                # 成功：记录到 progress.md
                self.three_files.update_progress(
                    log_entry=f"Successfully executed {tool_name}",
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
        
        Returns:
            Dict: Context 摘要
        """
        return {
            "session_id": self.session_id,
            "workspace_id": self.workspace_id,
            "message_count": self.context_manager.get_message_count(),
            "iteration_count": self.iteration_count,
            "token_usage": self.context_manager.get_token_usage(),
            "working_memory": {
                "task_plan": self.three_files.read_task_plan(),
                "file_paths": self.three_files.get_file_paths()
            }
        }
    
    def reset(self):
        """
        重置 Agent 状态（用于新对话）
        """
        self.context_manager.clear()
        self.tool_registry.reset_allowed_tools()
        self._current_skill_match = None
        self.iteration_count = 0
        logger.info("Agent state reset")
    
    # =========================================================================
    # Skill 系统集成
    # =========================================================================
    
    async def _match_and_inject_skill(self, user_message: str) -> None:
        """匹配 Skill 并注入 L2 指令
        
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
                    # 注入 Skill 指令到 Context
                    self.context_manager.inject_skill(
                        skill_id=match.skill_id,
                        display_name=skill_meta.display_name,
                        l2_instructions=l2_instructions,
                        allowed_tools=skill_meta.allowed_tools,
                    )
                    
                    # Action Space Pruning: 限制可用工具
                    if skill_meta.allowed_tools:
                        self.tool_registry.set_allowed_tools(skill_meta.allowed_tools)
                        logger.info(
                            f"Action Space Pruning: tools limited to {skill_meta.allowed_tools}"
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
