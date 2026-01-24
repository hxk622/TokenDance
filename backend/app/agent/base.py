"""
Agent 抽象基类

.. deprecated:: 2026-01
    BaseAgent 已废弃，请使用 AgentEngine 代替。

    统一架构设计：
    - 使用 AgentEngine.run_stream_with_planning() 获得带 Planning 的执行
    - 使用 AgentEngine.run() 获得传统状态机驱动的执行

    迁移指南：
    1. 替换 `class MyAgent(BaseAgent)` 为直接使用 `AgentEngine`
    2. 将 `_think()` 和 `_decide()` 逻辑移入 Skill 系统
    3. 使用 TaskScheduler + AtomicPlanner 进行任务编排

定义 Agent 的核心决策循环、思考链、工具调用等基础框架
"""
import json
import logging
import uuid
import warnings
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import asdict, is_dataclass
from typing import Any

from .context import AgentContext
from .llm import BaseLLM
from .memory import WorkingMemory
from .tools import BaseTool, ToolRegistry
from .tools.risk import RiskLevel

# from sqlalchemy.ext.asyncio import AsyncSession  # TODO: Re-enable when DB is ready
from .types import (
    ActionType,
    AgentAction,
    SSEEvent,
    SSEEventType,
    ToolCallRecord,
    ToolStatus,
)

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Agent 抽象基类

    .. deprecated:: 2026-01
        此类已废弃，请使用 AgentEngine 代替。
        AgentEngine 提供了统一的 Planning 架构，包括：
        - TaskScheduler: DAG 任务调度
        - AtomicPlanner: LLM 任务规划
        - 并行执行支持
        - 自动重规划

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
        self.current_message_id: str | None = None

        # Deprecation warning
        warnings.warn(
            "BaseAgent is deprecated and will be removed in a future version. "
            "Use AgentEngine.run_stream_with_planning() instead.",
            DeprecationWarning,
            stacklevel=2
        )

        logger.info(f"Agent initialized: {self.__class__.__name__}")

    # ==================== 主运行循环 ====================

    async def run(
        self,
        user_input: str,
        attachments: list[dict[str, Any]] | None = None
    ) -> AsyncGenerator[SSEEvent, None]:
        """主运行循环 - SSE 流式输出

        这是 Agent 的核心方法，负责：
        1. 添加用户消息
        2. Plan Recitation（重读计划）
        3. 思考（Thinking）
        4. 决策（Decide）
        5. 执行（Tool Call / Answer）
        6. 循环直到完成或停止

        Args:
            user_input: 用户输入文本
            attachments: 可选的附件列表，格式: [{"type": "image", "url": "data:image/...", "name": "..."}]

        Yields:
            SSEEvent: SSE 事件流
        """
        try:
            # 1. 添加用户消息（支持多模态）
            self.current_message_id = str(uuid.uuid4())
            await self._add_user_message(user_input, attachments)

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

                    # 2.3.1 如果有 thinking 内容，发送 AGENT_THINKING 事件
                    if action.thinking:
                        yield SSEEvent(
                            type=SSEEventType.AGENT_THINKING,
                            data={
                                'content': action.thinking,
                                'phase': 'reasoning',
                            }
                        )

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
                            "Final answer provided to user",
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
                    error_message = str(e)

                    # 检查是否是致命错误（应该停止而不是重启）
                    is_fatal = self._is_fatal_error(e, error_message)

                    if is_fatal:
                        logger.error(f"Fatal error detected: {error_type} - {error_message}")
                        # 发送致命错误事件
                        yield SSEEvent(
                            type=SSEEventType.ERROR,
                            data={
                                'message': error_message,
                                'type': error_type,
                                'fatal': True
                            }
                        )
                        # 停止执行
                        break

                    # 记录非致命错误
                    triggered = await self.memory.log_error(
                        error_type=error_type,
                        details=error_message
                    )

                    # 发送错误事件
                    yield SSEEvent(
                        type=SSEEventType.ERROR,
                        data={
                            'message': error_message,
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
        - 信任决策评估
        - HITL 确认（如果需要）
        - 2-Action Rule 检查
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

            # 3. 信任决策评估
            trust_result = await self._evaluate_trust(tool, tool_args)

            if trust_result.get('requires_confirmation', False):
                # 需要 HITL 确认
                yield SSEEvent(
                    type=SSEEventType.CONFIRM_REQUIRED,
                    data={
                        'action_id': tool_id,
                        'tool': tool_name,
                        'args': tool_args,
                        'description': tool.get_confirmation_description(**tool_args),
                        'risk_level': trust_result.get('risk_level', 'low'),
                        'reason': trust_result.get('reason', ''),
                        'operation_categories': trust_result.get('operation_categories', []),
                        'can_remember': trust_result.get('can_remember', True),
                    }
                )

                # TODO: 等待确认（需要外部状态管理）
                # 当 HITL 服务完全集成后，这里应该等待用户响应
                logger.info(f"Tool {tool_name} requires confirmation (risk={trust_result.get('risk_level')})")
                # 暂时假设确认通过
            else:
                # 自动授权 - 记录日志
                logger.info(
                    f"Tool {tool_name} auto-approved: {trust_result.get('reason', 'within trust level')}"
                )

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
            result_data = await tool.execute(**tool_args)

            # 规范化结果为 dict（支持 dict 和 dataclass）
            if isinstance(result_data, dict):
                result_dict = result_data
            elif is_dataclass(result_data) and not isinstance(result_data, type):
                result_dict = asdict(result_data)
            else:
                result_dict = {"result": str(result_data)}

            # 序列化为 JSON 字符串
            result_str = json.dumps(result_dict, ensure_ascii=False, indent=2)

            # 5. 成功 - 发送 tool_result 事件
            yield SSEEvent(
                type=SSEEventType.TOOL_RESULT,
                data={
                    'id': tool_id,
                    'status': ToolStatus.SUCCESS.value,
                    'result': result_str[:500] if len(result_str) > 500 else result_str  # 限制长度
                }
            )

            # 6. 记录到 context
            tool_call_record = ToolCallRecord(
                id=tool_id,
                name=tool_name,
                args=tool_args,
                status=ToolStatus.SUCCESS,
                result=result_str
            )
            self.context.add_tool_call(tool_call_record)

            # 7. 记录到 progress.md
            await self.memory.log_action(
                f"Tool Call: {tool_name}",
                f"Args: {tool_args}\nResult: {result_str[:200]}...",
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

        # 如果是研究报告，发送 RESEARCH_REPORT_READY 事件携带 citations
        if action.data and action.data.get("report_type") == "research":
            yield SSEEvent(
                type=SSEEventType.RESEARCH_REPORT_READY,
                data={
                    'report_type': 'research',
                    'citations': action.data.get('citations', []),
                }
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

    async def _evaluate_trust(self, tool: BaseTool, tool_args: dict) -> dict:
        """评估工具调用的信任决策

        这是一个简化版本的信任评估，当数据库完全集成后，
        应该使用 TrustService 进行完整的信任决策。

        Args:
            tool: 工具实例
            tool_args: 工具调用参数

        Returns:
            dict: 信任决策结果，包含：
                - requires_confirmation: 是否需要确认
                - reason: 决策原因
                - risk_level: 风险等级
                - operation_categories: 操作类别列表
                - can_remember: 是否允许记住选择
        """
        # 获取动态风险等级和操作类别
        risk_level = tool.get_risk_level(**tool_args)
        operation_categories = tool.get_operation_categories(**tool_args)

        # 向后兼容：如果工具强制需要确认
        if tool.requires_confirmation:
            return {
                'requires_confirmation': True,
                'reason': '工具配置为强制确认',
                'risk_level': risk_level.value,
                'operation_categories': [c.value for c in operation_categories],
                'can_remember': risk_level != RiskLevel.CRITICAL,
            }

        # CRITICAL 风险等级始终需要确认
        if risk_level == RiskLevel.CRITICAL:
            return {
                'requires_confirmation': True,
                'reason': '极高风险操作，需要确认',
                'risk_level': risk_level.value,
                'operation_categories': [c.value for c in operation_categories],
                'can_remember': False,
            }

        # 默认信任策略：NONE 和 LOW 风险自动执行
        # TODO: 当数据库集成后，从 TrustConfig 读取配置
        default_auto_approve_levels = [RiskLevel.NONE, RiskLevel.LOW]

        if risk_level in default_auto_approve_levels:
            return {
                'requires_confirmation': False,
                'reason': f'风险等级 {risk_level.value} 在自动授权范围内',
                'risk_level': risk_level.value,
                'operation_categories': [c.value for c in operation_categories],
                'can_remember': True,
            }

        # 其他情况需要确认
        return {
            'requires_confirmation': True,
            'reason': '操作未预授权',
            'risk_level': risk_level.value,
            'operation_categories': [c.value for c in operation_categories],
            'can_remember': True,
        }

    async def _add_user_message(
        self,
        content: str,
        attachments: list[dict[str, Any]] | None = None
    ) -> None:
        """添加用户消息到 context，支持多模态内容

        Args:
            content: 消息文本内容
            attachments: 可选的附件列表，格式: [{"type": "image", "url": "data:image/..."}]
        """
        # 构建消息内容
        if attachments:
            # 多模态消息：图片 + 文本
            message_content = []

            # 先添加图片
            for attachment in attachments:
                if attachment.get("type") == "image" and attachment.get("url"):
                    message_content.append({
                        "type": "image_url",
                        "image_url": {"url": attachment["url"]}
                    })
                    logger.info(f"Image attachment added: {attachment.get('name', 'unnamed')}")

            # 再添加文本
            if content:
                message_content.append({
                    "type": "text",
                    "text": content
                })

            # 如果只有图片没有文本，添加默认提示
            if not content and message_content:
                message_content.append({
                    "type": "text",
                    "text": "请分析这张图片"
                })

            self.context.messages.append({
                "role": "user",
                "content": message_content
            })
            logger.info(f"Multimodal message added: {len(attachments)} images, text: {content[:30] if content else '(none)'}...")
        else:
            # 纯文本消息
            self.context.messages.append({
                "role": "user",
                "content": content
            })
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

    def _is_fatal_error(self, exception: Exception, error_message: str) -> bool:
        """判断是否是致命错误（应该停止而不是重启）

        致命错误包括：
        - API速率限制（429）- 重试也无法解决
        - 认证失败（401, 403）- 配置问题
        - 配额耗尽 - 需要人工介入
        - ValueError包含特定关键词 - 表示不可恢复的错误

        Args:
            exception: 异常对象
            error_message: 错误消息

        Returns:
            bool: 是否是致命错误
        """
        # 检查错误类型
        error_type = exception.__class__.__name__

        # HTTPStatusError - 检查具体状态码
        if error_type == 'HTTPStatusError':
            # 429 Too Many Requests - 速率限制
            if '429' in error_message or 'Too Many Requests' in error_message:
                logger.warning("Detected 429 rate limit error - marking as fatal")
                return True
            # 401 Unauthorized - 认证失败
            if '401' in error_message or 'Unauthorized' in error_message:
                logger.warning("Detected 401 auth error - marking as fatal")
                return True
            # 403 Forbidden - 权限不足
            if '403' in error_message or 'Forbidden' in error_message:
                logger.warning("Detected 403 permission error - marking as fatal")
                return True

        # ValueError - 检查特定消息
        if error_type == 'ValueError':
            fatal_keywords = [
                'rate limit exceeded',
                'quota exceeded',
                'insufficient credits',
                'API key invalid',
                'authentication failed'
            ]
            for keyword in fatal_keywords:
                if keyword.lower() in error_message.lower():
                    logger.warning(f"Detected fatal ValueError with keyword '{keyword}'")
                    return True

        # 默认不是致命错误
        return False

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
