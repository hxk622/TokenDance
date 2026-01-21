"""
ResearchAgent - 研究型 Agent

支持使用工具进行信息收集和研究
"""
import logging
from collections.abc import AsyncGenerator

from ..base import BaseAgent
from ..types import ActionType, AgentAction, SSEEvent, SSEEventType

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """研究型 Agent

    特点：
    - 支持工具调用（web_search, read_url）
    - 自动记录发现到 findings.md（2-Action Rule）
    - 生成结构化研究报告

    用途：
    - 信息研究和收集
    - 事实核查
    - 深度调研任务
    """

    async def _think(self) -> AsyncGenerator[SSEEvent, None]:
        """思考过程 - ResearchAgent 版本

        使用 LLM 分析当前情况并制定行动计划

        Yields:
            SSEEvent: thinking 事件
        """
        logger.debug("ResearchAgent thinking...")

        yield SSEEvent(
            type=SSEEventType.THINKING,
            data={'content': '🤔 Analyzing task and planning approach...\\n'}
        )

        # 构造思考提示
        system_prompt = """You are a research assistant AI. Analyze the user's question and:
1. Identify what information is needed
2. Determine which tools to use (web_search, read_url)
3. Plan your research approach

Be concise in your thinking."""

        # 使用 LLM 进行思考
        thinking_content = ""
        async for chunk in self.llm.stream(
            messages=self.context.messages,
            system=system_prompt
        ):
            thinking_content += chunk
            yield SSEEvent(
                type=SSEEventType.THINKING,
                data={'content': chunk}
            )

        # 保存思考内容
        self.context.append_thinking(thinking_content)

        logger.debug("Thinking complete")

    async def _decide(self) -> AgentAction:
        """决策 - ResearchAgent 版本

        基于思考结果决定下一步行动：
        - 调用工具收集信息
        - 生成最终回答

        Returns:
            AgentAction: 决策动作
        """
        logger.debug("ResearchAgent making decision...")

        # 获取可用工具列表
        tool_definitions = self.tools.to_llm_format()

        if not tool_definitions:
            # 没有工具，直接回答
            logger.warning("No tools available, falling back to direct answer")
            return await self._generate_answer()

        # 构造决策提示
        system_prompt = """You are a research assistant. Based on the conversation and your thinking:

1. If you need more information, use the available tools:
   - web_search: Search for current information
   - read_url: Read detailed content from a specific URL

2. If you have enough information, provide a comprehensive answer.

3. IMPORTANT: When recording findings after using tools, be concise but informative.

Respond with either a tool call OR a final answer."""

        # 调用 LLM 进行决策（支持 Function Calling）
        response = await self.llm.complete(
            messages=self.context.messages,
            system=system_prompt,
            tools=tool_definitions
        )

        # 检查是否有工具调用
        if response.tool_calls:
            # 返回工具调用动作
            tool_call = response.tool_calls[0]  # 暂时只支持单个工具调用

            return AgentAction(
                type=ActionType.TOOL_CALL,
                tool_name=tool_call["name"],
                tool_args=tool_call["input"],
                tool_call_id=tool_call["id"]
            )

        # 没有工具调用，返回最终回答
        answer = response.content.strip()

        return AgentAction(
            type=ActionType.ANSWER,
            answer=answer
        )

    async def _generate_answer(self) -> AgentAction:
        """生成最终回答（无工具情况下的后备方案）

        Returns:
            AgentAction: 回答动作
        """
        system_prompt = "You are a helpful research assistant. Provide a clear and concise answer based on the conversation."

        response = await self.llm.complete(
            messages=self.context.messages,
            system=system_prompt
        )

        return AgentAction(
            type=ActionType.ANSWER,
            answer=response.content.strip()
        )


# 便捷工厂函数
async def create_research_agent(
    context,
    llm,
    tools,
    memory,
    db,
    max_iterations: int = 20
):
    """创建 ResearchAgent 实例

    Args:
        context: AgentContext
        llm: BaseLLM
        tools: ToolRegistry
        memory: WorkingMemory
        db: AsyncSession
        max_iterations: 最大迭代次数（研究任务可能需要更多迭代）

    Returns:
        ResearchAgent: Agent 实例
    """
    agent = ResearchAgent(
        context=context,
        llm=llm,
        tools=tools,
        memory=memory,
        db=db,
        max_iterations=max_iterations
    )

    logger.info(f"ResearchAgent created: {agent}")
    return agent
