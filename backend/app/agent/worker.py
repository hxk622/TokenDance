"""
Agent Worker - 持续运行的 Agent 执行器

职责:
1. 监听 Redis 队列,接收执行任务
2. 加载 Conversation 的完整上下文
3. 执行 Agent 并流式发送事件
4. 更新 shared_memory
5. 保存执行结果
"""
import json
import logging

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent import AgentContext, create_working_memory
from app.agent.agents.deep_research import DeepResearchAgent
from app.agent.llm.router import TaskType
from app.agent.llm.unified_router import get_router
from app.agent.tools import ToolRegistry
from app.agent.tools.init_tools import register_builtin_tools
from app.core.config import Settings
from app.repositories.message_repository import MessageRepository
from app.services.conversation_service import ConversationService
from app.services.session_service import SessionService
from app.services.sse_event_store import SSEEventStore

logger = logging.getLogger(__name__)


class AgentWorker:
    """
    Agent Worker - 持续运行的 Agent 执行器

    设计理念:
    1. 长期运行: Worker 持续监听 Redis 队列
    2. 上下文感知: 加载完整的 Conversation 上下文
    3. 状态持久化: 定期保存 checkpoint
    4. 智能记忆: 提取和更新 shared_memory
    """

    def __init__(
        self,
        redis: Redis,
        db: AsyncSession,
        settings: Settings,
        event_store: SSEEventStore,
    ):
        self.redis = redis
        self.db = db
        self.settings = settings
        self.event_store = event_store
        self.running_agents: dict[str, DeepResearchAgent] = {}

    async def start(self):
        """
        启动 Worker,监听执行队列

        持续监听 Redis 的 "agent:execute" 频道
        """
        logger.info("agent_worker_started")

        pubsub = self.redis.pubsub()
        await pubsub.subscribe("agent:execute")

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await self.execute_turn(
                            conversation_id=data["conversation_id"],
                            turn_id=data["turn_id"],
                            user_input=data["user_input"],
                        )
                    except Exception as e:
                        logger.error(f"Failed to execute turn: {e}", exc_info=True)
        finally:
            await pubsub.unsubscribe("agent:execute")
            logger.info("agent_worker_stopped")

    async def execute_turn(
        self,
        conversation_id: str,
        turn_id: str,
        user_input: str,
    ):
        """
        执行一个 Turn

        核心流程:
        1. 加载 Conversation 的完整上下文
        2. 加载 shared_memory 和历史消息
        3. 创建 Session 和 Agent
        4. 执行 Agent 并流式发送事件
        5. 提取和更新 shared_memory
        6. 保存结果
        """
        conversation_service = ConversationService(self.db)
        session_service = SessionService(self.db)
        message_repo = MessageRepository(self.db)

        try:
            # 1. 加载上下文
            conversation = await conversation_service.get_conversation(
                conversation_id,
                include_turns=True,
            )
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            from app.models.project import Project
            from app.models.workspace import Workspace

            project = await self.db.get(Project, conversation.project_id)
            if not project:
                raise ValueError(f"Project {conversation.project_id} not found")

            workspace = await self.db.get(Workspace, project.workspace_id)
            if not workspace:
                raise ValueError(f"Workspace {project.workspace_id} not found")

            # 2. 加载历史消息 (最近 20 条)
            message_history = await conversation_service.get_message_history(
                conversation_id,
                limit=20,
            )

            # 3. 加载 shared_memory
            shared_memory = conversation.shared_memory or {}

            # 4. 创建 Session
            session = await session_service.create_session(
                workspace_id=project.workspace_id,
                title=f"Turn {conversation.turn_count}",
            )
            session.conversation_id = conversation_id
            session.turn_id = turn_id
            await self.db.commit()

            # 5. 更新 Turn 状态
            from app.models.turn import Turn
            turn = await self.db.get(Turn, turn_id)
            if not turn:
                raise ValueError(f"Turn {turn_id} not found")

            turn.primary_session_id = session.id
            turn.start()
            await self.db.commit()

            # 6. 创建 Working Memory (从 shared_memory 恢复)
            workspace_path = self._get_workspace_path(project.workspace_id, conversation.id)
            memory = await create_working_memory(
                workspace_path=workspace_path,
                session_id=session.id,
                initial_task=user_input,
            )

            # 注入 shared_memory 到 memory
            if shared_memory:
                await self._inject_shared_memory(memory, shared_memory, message_history)

            # 7. 创建 Agent Context
            context = AgentContext(
                session_id=session.id,
                user_id=workspace.owner_id,
                workspace_id=project.workspace_id,
            )

            # 8. 创建 Agent
            tools = ToolRegistry()
            register_builtin_tools(tools)

            router = get_router()
            llm = await router.get_llm(
                task_type=TaskType.DEEP_RESEARCH,
                max_tokens=4096,
            )

            agent = DeepResearchAgent(
                context=context,
                llm=llm,
                tools=tools,
                memory=memory,
                db=self.db,
                max_iterations=50,
            )

            # 9. 执行 Agent 并流式发送事件
            total_tokens = 0
            assistant_content_parts = []

            async for event in agent.run(user_input):
                # 存储事件到 event_store
                await self.event_store.store_event(
                    turn_id,
                    event.type.value,
                    event.data,
                )

                # 收集响应内容
                if event.type.value == "content":
                    assistant_content_parts.append(event.data.get("content", ""))
                elif event.type.value == "done":
                    total_tokens = event.data.get("tokens_used", 0)

            # 10. 保存 Assistant Message
            assistant_content = "".join(assistant_content_parts)
            assistant_message = await message_repo.create_assistant_message(
                session_id=session.id,
                content=assistant_content,
                tokens_used=total_tokens,
            )
            assistant_message.conversation_id = conversation_id
            assistant_message.turn_id = turn_id
            await self.db.commit()

            # 11. 更新 Turn
            turn.complete(assistant_message.id, total_tokens)
            turn.assistant_response = assistant_content[:5000]  # 截断存储
            await self.db.commit()

            # 12. 提取和更新 shared_memory
            updated_memory = await self._extract_and_merge_memory(
                conversation,
                agent,
                user_input,
                assistant_content,
            )
            await conversation_service.update_shared_memory(
                conversation_id,
                updated_memory,
                merge=True,
            )

            # 13. 更新 Conversation 统计
            conversation.total_tokens_used += total_tokens
            conversation.message_count += 1  # assistant message
            await self.db.commit()

            logger.info(
                "turn_executed_successfully",
                conversation_id=conversation_id,
                turn_id=turn_id,
                turn_number=turn.turn_number,
                tokens_used=total_tokens,
            )

        except Exception as e:
            logger.error(f"Turn execution failed: {e}", exc_info=True)

            # 标记 Turn 为失败
            try:
                turn = await self.db.get(Turn, turn_id)
                if turn:
                    turn.fail(str(e))
                    await self.db.commit()
            except Exception as update_error:
                logger.error(f"Failed to update turn status: {update_error}")

    async def _inject_shared_memory(
        self,
        memory,
        shared_memory: dict,
        message_history: list,
    ):
        """
        将 shared_memory 注入到 Working Memory

        在 task_plan.md 中添加上下文信息
        """
        context_parts = []

        # 1. 历史消息摘要
        if message_history:
            context_parts.append("## 对话历史摘要\n")
            for msg in message_history[-5:]:  # 最近 5 条
                role = "用户" if msg.role == "user" else "助手"
                content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                context_parts.append(f"- **{role}**: {content}\n")

        # 2. 关键事实
        if shared_memory.get("key_facts"):
            context_parts.append("\n## 已知关键事实\n")
            for fact in shared_memory["key_facts"][-5:]:
                context_parts.append(f"- {fact['fact']} (置信度: {fact['confidence']})\n")

        # 3. 实体
        if shared_memory.get("entities"):
            context_parts.append("\n## 相关实体\n")
            for entity_type, entities in shared_memory["entities"].items():
                context_parts.append(f"- {entity_type}: {', '.join(entities[:5])}\n")

        # 4. 主题
        if shared_memory.get("topics"):
            context_parts.append(f"\n## 讨论主题\n{', '.join(shared_memory['topics'])}\n")

        # 将上下文添加到 task_plan
        if context_parts:
            context_text = "\n".join(context_parts)
            current_plan = await memory.read_task_plan()
            updated_plan = f"{context_text}\n\n---\n\n{current_plan}"
            await memory.write_task_plan(updated_plan)

    async def _extract_and_merge_memory(
        self,
        conversation,
        agent: DeepResearchAgent,
        user_input: str,
        assistant_response: str,
    ) -> dict:
        """
        从 Agent 执行结果中提取关键信息,更新 shared_memory

        提取:
        1. key_facts: 从 findings 中提取
        2. entities: 从对话中识别
        3. topics: 从用户输入中提取
        4. context: 更新当前上下文
        """
        memory_update = {}

        # 1. 提取 key_facts (从 findings)
        try:
            findings = await agent.memory.read_findings()
            if findings and len(findings) > 100:
                # 简单提取: 将 findings 的每一段作为一个 fact
                # 生产环境应该使用 LLM 提取结构化信息
                facts = []
                for line in findings.split("\n"):
                    line = line.strip()
                    if line and len(line) > 20 and not line.startswith("#"):
                        facts.append({
                            "fact": line[:200],  # 截断
                            "source": f"turn_{conversation.turn_count}",
                            "confidence": 0.8,
                            "timestamp": agent.memory.last_plan_read_time.isoformat() if agent.memory.last_plan_read_time else None,
                        })

                if facts:
                    memory_update["key_facts"] = facts[:10]  # 最多 10 条
        except Exception as e:
            logger.warning(f"Failed to extract key_facts: {e}")

        # 2. 提取 topics (从用户输入)
        # 简单实现: 提取关键词
        topics = []
        keywords = ["AI Agent", "市场", "规模", "增长", "预测", "调研", "分析"]
        for keyword in keywords:
            if keyword in user_input or keyword in assistant_response:
                topics.append(keyword)

        if topics:
            memory_update["topics"] = topics

        # 3. 更新 context
        memory_update["context"] = {
            "last_user_input": user_input[:200],
            "last_assistant_response": assistant_response[:200],
            "current_turn": conversation.turn_count,
        }

        return memory_update

    def _get_workspace_path(self, workspace_id: str, conversation_id: str) -> str:
        """获取工作空间路径"""
        import os
        return os.path.join(
            self.settings.SESSIONS_DATA_PATH,
            workspace_id,
            conversation_id,
        )


# 启动 Worker 的入口函数
async def start_agent_worker(
    redis: Redis,
    db: AsyncSession,
    settings: Settings,
    event_store: SSEEventStore,
):
    """
    启动 Agent Worker

    这个函数应该在后台进程中运行
    """
    worker = AgentWorker(redis, db, settings, event_store)
    await worker.start()
