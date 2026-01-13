"""
Agent 抽象基类

定义 Agent 的核心决策循环、思考链、工具调用等基础框架
"""
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, List, Dict, Any
import uuid
import logging
from datetime import datetime

# from sqlalchemy.ext.asyncio import AsyncSession  # TODO: Re-enable when DB is ready

from .types import (
    SSEEvent,
    SSEEventType,
    AgentAction,
    ActionType,
    ToolStatus,
    ToolCallRecord,
)
from .context import AgentContext
from .memory import WorkingMemory
from .tools import ToolRegistry, BaseTool
from .llm import BaseLLM, LLMMessage

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Agent 抽象基类
    
    定义 Agent 的核心决策循环框架，包括：
    - 思考链（Chain of Thought）
    - 工具调用编排
    - Plan Recitation
    - HITL 确认
    - Working Memory 集成
    
    子类需要实现：
    - _think(): 思考过程
    - _decide(): 决策逻辑
    """
    
    def __init__(
        self,
        context: AgentContext,
        llm: BaseLLM,
        tools: ToolRegistry,
        memory: WorkingMemory,
        db: Any,  # AsyncSession, TODO: Re-enable type hint
        max_iterations: int = 50
    ):
        """初始化 Agent
        
        Args:
            context: Agent 运行时上下文
            llm: LLM 客户端
            tools: 工具注册表
            memory: Working Memory（三文件系统）
            db: 数据库会话
            max_iterations: 最大迭代次数
        """
        self.context = context
        self.llm = llm
        self.tools = tools
        self.memory = memory
        self.db = db
        self.max_iterations = max_iterations
        
        self.stopped = False
        self.current_message_id: Optional[str] = None
        
        logger.info(f"Agent initialized: {self.__class__.__name__}")
    
    # ==================== 主运行循环 ====================
    
    async def run(self, user_input: str) -> AsyncGenerator[SSEEvent, None]:
        """主运行循环 - SSE 流式输出
        
        这是 Agent 的核心方法，负责：
        1. 添加用户消息
        2. Plan Recitation（重读计划）
        3. 思考（Thinking）
        4. 决策（Decide）
        5. 执行（Tool Call / Answer）
        6. 循环直到完成或停止
        
        Args:
            user_input: 用户输入
            
        Yields:
            SSEEvent: SSE 事件流
        """
        try:
            # 1. 添加用户消息
            self.current_message_id = str(uuid.uuid4())
            await self._add_user_message(user_input)
            
            # 记录到 progress.md
            await self.memory.log_action(
                "User Input Received",
                user_input,
                status="📥"
            )
            
            # 2. 主循环
            while self._should_continue():
                self.context.increment_iteration()
                
                try:
                    # 2.1 Plan Recitation
                    if self.memory.should_recite_plan():
                        await self._recite_plan()
                    
                    # 2.2 思考（Thinking）
                    async for thinking_event in self._think():
                        yield thinking_event
                    
                    # 2.3 决策
                    action = await self._decide()
                    
                    # 2.4 执行决策
                    if action.type == ActionType.TOOL_CALL:
                        # 工具调用
                        async for tool_event in self._execute_tool(action):
                            yield tool_event
                    
                    elif action.type == ActionType.ANSWER:
                        # 最终回答
                        async for content_event in self._stream_answer(action):
                            yield content_event
                        
                        # 记录到 progress.md
                        await self.memory.log_action(
                            "Answer Generated",
                            f"Final answer provided to user",
                            status="✅"
                        )
                        break  # 完成
                    
                    elif action.type == ActionType.CONFIRM_REQUIRED:
                        # HITL 确认
                        yield SSEEvent(
                            type=SSEEventType.CONFIRM_REQUIRED,
                            data=action.data or {}
                        )
                        
                        # 等待确认（暂时跳过，需要外部处理）
                        logger.info("HITL confirmation required")
                        break
                
                except Exception as e:
                    logger.error(f"Error in agent loop: {e}", exc_info=True)
                    
                    # 记录错误
                    error_type = e.__class__.__name__
                    triggered = await self.memory.log_error(
                        error_type=error_type,
                        details=str(e)
                    )
                    
                    # 发送错误事件
                    yield SSEEvent(
                        type=SSEEventType.ERROR,
                        data={
                            'message': str(e),
                            'type': error_type
                        }
                    )
                    
                    # 如果触发 3-Strike，重启
                    if triggered:
                        logger.warning("3-Strike triggered, rebooting...")
                        async for reboot_event in self._reboot_test():
                            yield reboot_event
                    else:
                        # 否则继续
                        continue
            
            # 3. 完成
            yield SSEEvent(
                type=SSEEventType.DONE,
                data={
                    'status': 'completed' if not self.stopped else 'stopped',
                    'message_id': self.current_message_id,
                    'tokens_used': self.context.tokens_used,
                    'iterations': self.context.iteration
                }
            )
            
        except Exception as e:
            logger.error(f"Fatal error in agent run: {e}", exc_info=True)
            yield SSEEvent(
                type=SSEEventType.ERROR,
                data={
                    'message': f"Fatal error: {str(e)}",
                    'type': 'FatalError'
                }
            )
    
    # ==================== 抽象方法（子类实现） ====================
    
    @abstractmethod
    async def _think(self) -> AsyncGenerator[SSEEvent, None]:
        """思考过程
        
        子类必须实现此方法来定义思考逻辑。
        
        Yields:
            SSEEvent: thinking 事件
        """
        pass
    
    @abstractmethod
    async def _decide(self) -> AgentAction:
        """决策
        
        子类必须实现此方法来定义决策逻辑。
        
        Returns:
            AgentAction: 决策结果（工具调用/回答/确认）
        """
        pass
    
    # ==================== Plan Recitation ====================
    
    async def _recite_plan(self) -> None:
        """Plan Recitation - 重读任务计划
        
        从 task_plan.md 读取计划并追加到 LLM context
        """
        plan_content = await self.memory.read_task_plan()
        
        if plan_content and len(plan_content) > 50:  # 不是空文件
            # 追加到 context（作为系统消息）
            # 注意：这里只是示例，实际需要集成到 LLM 调用中
            logger.info("Plan Recitation: Plan read and ready to append to context")
            
            # 记录到 progress.md
            await self.memory.log_action(
                "Plan Recitation",
                "Task plan reviewed",
                status="📖"
            )
    
    # ==================== 工具调用 ====================
    
    async def _execute_tool(
        self,
        action: AgentAction
    ) -> AsyncGenerator[SSEEvent, None]:
        """执行工具调用
        
        包含：
        - 2-Action Rule 检查
        - HITL 确认（如果需要）
        - 工具执行
        - 3-Strike Protocol 错误处理
        
        Args:
            action: 工具调用动作
            
        Yields:
            SSEEvent: 工具相关事件
        """
        tool_name = action.tool_name
        tool_args = action.tool_args or {}
        tool_id = str(uuid.uuid4())
        
        logger.info(f"Executing tool: {tool_name}")
        
        # 1. 发送 tool_call pending 事件
        yield SSEEvent(
            type=SSEEventType.TOOL_CALL,
            data={
                'id': tool_id,
                'name': tool_name,
                'args': tool_args,
                'status': ToolStatus.PENDING.value
            }
        )
        
        try:
            # 2. 获取工具
            tool: BaseTool = self.tools.get(tool_name)
            
            # 3. HITL 确认检查
            if tool.requires_confirmation:
                yield SSEEvent(
                    type=SSEEventType.CONFIRM_REQUIRED,
                    data={
                        'action_id': tool_id,
                        'tool': tool_name,
                        'args': tool_args,
                        'description': tool.description
                    }
                )
                
                # TODO: 等待确认（需要外部状态管理）
                logger.info(f"Tool {tool_name} requires confirmation")
                # 暂时假设确认通过
            
            # 4. 执行工具 - running 状态
            yield SSEEvent(
                type=SSEEventType.TOOL_CALL,
                data={
                    'id': tool_id,
                    'status': ToolStatus.RUNNING.value
                }
            )
            
            # 验证参数
            tool.validate_args(tool_args)
            
            # 执行
            result = await tool.execute(**tool_args)
            
            # 5. 成功 - 发送 tool_result 事件
            yield SSEEvent(
                type=SSEEventType.TOOL_RESULT,
                data={
                    'id': tool_id,
                    'status': ToolStatus.SUCCESS.value,
                    'result': result[:500] if len(result) > 500 else result  # 限制长度
                }
            )
            
            # 6. 记录到 context
            tool_call_record = ToolCallRecord(
                id=tool_id,
                name=tool_name,
                args=tool_args,
                status=ToolStatus.SUCCESS,
                result=result
            )
            self.context.add_tool_call(tool_call_record)
            
            # 7. 记录到 progress.md
            await self.memory.log_action(
                f"Tool Call: {tool_name}",
                f"Args: {tool_args}\nResult: {result[:200]}...",
                status="🔧"
            )
            
            # 8. 检查 2-Action Rule（信息获取类工具）
            if tool_name in ['web_search', 'read_url', 'read_file', 'code_execute']:
                if self.memory.should_record_finding():
                    # 提示应该记录发现
                    yield SSEEvent(
                        type=SSEEventType.THINKING,
                        data={
                            'content': '\n⚠️ [2-Action Rule] Time to record findings to findings.md\n'
                        }
                    )
        
        except Exception as e:
            logger.error(f"Tool execution failed: {e}", exc_info=True)
            
            # 发送失败事件
            yield SSEEvent(
                type=SSEEventType.TOOL_RESULT,
                data={
                    'id': tool_id,
                    'status': ToolStatus.ERROR.value,
                    'error': str(e)
                }
            )
            
            # 记录错误（3-Strike Protocol）
            error_type = e.__class__.__name__
            triggered = await self.memory.log_error(
                error_type=error_type,
                details=str(e),
                tool_name=tool_name
            )
            
            if triggered:
                # 3-Strike 触发，发送通知
                yield SSEEvent(
                    type=SSEEventType.ERROR,
                    data={
                        'message': f'3-Strike Protocol triggered for {error_type}',
                        'type': '3-Strike',
                        'should_reboot': True
                    }
                )
    
    # ==================== 回答生成 ====================
    
    async def _stream_answer(
        self,
        action: AgentAction
    ) -> AsyncGenerator[SSEEvent, None]:
        """流式生成最终回答
        
        Args:
            action: 回答动作
            
        Yields:
            SSEEvent: content 事件
        """
        answer = action.answer or ""
        
        # 简单实现：分块发送
        # TODO: 实际应该调用 LLM 流式生成
        chunk_size = 20
        for i in range(0, len(answer), chunk_size):
            chunk = answer[i:i+chunk_size]
            yield SSEEvent(
                type=SSEEventType.CONTENT,
                data={'content': chunk}
            )
    
    # ==================== 5-Question Reboot Test ====================
    
    async def _reboot_test(self) -> AsyncGenerator[SSEEvent, None]:
        """5-Question Reboot Test
        
        当 3-Strike 触发时，通过 5 个问题重新找回方向：
        1. What is my original goal?
        2. What have I tried so far?
        3. What went wrong?
        4. What should I try differently?
        5. Should I ask for human help?
        
        Yields:
            SSEEvent: thinking 事件
        """
        logger.info("Starting 5-Question Reboot Test")
        
        yield SSEEvent(
            type=SSEEventType.THINKING,
            data={'content': '\n🔄 5-Question Reboot Test\n\n'}
        )
        
        # 1. Read task_plan.md
        task_plan = await self.memory.read_task_plan()
        yield SSEEvent(
            type=SSEEventType.THINKING,
            data={'content': f'1. Original Goal:\n{task_plan[:300]}...\n\n'}
        )
        
        # 2. Read progress.md (last 500 chars)
        progress = await self.memory.read_progress(last_n_chars=500)
        yield SSEEvent(
            type=SSEEventType.THINKING,
            data={'content': f'2. What I\'ve tried:\n{progress}\n\n'}
        )
        
        # 3-5. 需要 LLM 思考
        # TODO: 调用 LLM 回答剩余问题
        yield SSEEvent(
            type=SSEEventType.THINKING,
            data={
                'content': '3-5. Analyzing errors and considering alternative approaches...\n'
            }
        )
        
        # 重置错误追踪器
        self.memory.reset_error_tracker()
        
        yield SSEEvent(
            type=SSEEventType.THINKING,
            data={'content': '\n✅ Reboot complete. Resuming execution.\n\n'}
        )
    
    # ==================== 辅助方法 ====================
    
    async def _add_user_message(self, content: str) -> None:
        """添加用户消息到 context
        
        Args:
            content: 消息内容
        """
        # 添加到 context.messages
        self.context.messages.append({
            "role": "user",
            "content": content
        })
        
        # TODO: 实际需要创建 Message 对象并存入数据库
        logger.info(f"User message added: {content[:50]}...")
    
    def _should_continue(self) -> bool:
        """判断是否应该继续执行
        
        Returns:
            bool: 是否继续
        """
        if self.stopped:
            logger.info("Agent stopped by user")
            return False
        
        if self.context.iteration >= self.max_iterations:
            logger.warning(f"Max iterations reached: {self.max_iterations}")
            return False
        
        if not self.context.should_continue():
            logger.warning("Context signals to stop")
            return False
        
        return True
    
    async def stop(self) -> None:
        """停止 Agent 执行"""
        self.stopped = True
        logger.info("Agent stop requested")
        
        await self.memory.log_action(
            "Agent Stopped",
            "Execution stopped by user",
            status="⏹️"
        )
    
    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}("
            f"session={self.context.session_id[:8]}, "
            f"iteration={self.context.iteration}/{self.max_iterations})>"
        )
