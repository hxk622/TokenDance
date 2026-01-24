"""
BasicAgent - 简单对话 Agent

最简单的 Agent 实现，用于测试基础流程。
不使用工具调用，只进行简单的对话。
"""
import logging
from collections.abc import AsyncGenerator

from ..base import BaseAgent
from ..types import ActionType, AgentAction, SSEEvent, SSEEventType

logger = logging.getLogger(__name__)


class BasicAgent(BaseAgent):
    """基础对话 Agent

    特点：
    - 不使用工具
    - 简单的思考过程
    - 直接生成回答

    用途：
    - 测试 Agent 基础流程
    - 简单问答场景
    - 调试和演示
    """

    async def _think(self) -> AsyncGenerator[SSEEvent, None]:
        """思考过程 - BasicAgent 版本

        简单的思考逻辑：
        1. 分析用户输入
        2. 确定回答策略

        Yields:
            SSEEvent: thinking 事件
        """
        logger.debug("BasicAgent thinking...")

        # 发送思考开始
        yield SSEEvent(
            type=SSEEventType.THINKING,
            data={'content': 'Analyzing your question...\n'}
        )

        # BasicAgent 的思考比较简单，直接记录即可
        if self.context.messages:
            last_content = self.context.messages[-1].get('content', '')
            # 处理多模态消息：提取文本部分
            if isinstance(last_content, list):
                text_parts = [p.get('text', '') for p in last_content if p.get('type') == 'text']
                image_count = sum(1 for p in last_content if p.get('type') == 'image_url')
                text_summary = ' '.join(text_parts) if text_parts else '(图片)'
                thinking_content = f"User question: {text_summary} [+{image_count} image(s)]"
            else:
                thinking_content = f"User question: {last_content}"
        else:
            thinking_content = "User question: N/A"
        self.context.append_thinking(thinking_content)

        logger.debug("Thinking complete")

    async def _decide(self) -> AgentAction:
        """决策 - BasicAgent 版本

        BasicAgent 总是选择直接回答，不使用工具。

        Returns:
            AgentAction: 回答动作
        """
        logger.debug("BasicAgent making decision...")

        # BasicAgent 不使用工具，使用 LLM 生成回答
        response = await self.llm.complete(
            messages=self.context.messages,
            system="You are a helpful AI assistant. Provide clear and concise answers."
        )

        answer = response.content.strip()

        return AgentAction(
            type=ActionType.ANSWER,
            answer=answer
        )


# 便捷工厂函数
async def create_basic_agent(
    context,
    llm,
    tools,
    memory,
    db,
    max_iterations: int = 10  # BasicAgent 通常不需要很多迭代
):
    """创建 BasicAgent 实例

    Args:
        context: AgentContext
        llm: BaseLLM
        tools: ToolRegistry
        memory: WorkingMemory
        db: AsyncSession
        max_iterations: 最大迭代次数

    Returns:
        BasicAgent: Agent 实例
    """
    agent = BasicAgent(
        context=context,
        llm=llm,
        tools=tools,
        memory=memory,
        db=db,
        max_iterations=max_iterations
    )

    logger.info(f"BasicAgent created: {agent}")
    return agent
