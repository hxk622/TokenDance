"""
Conversation Service - 对话服务

提供多轮对话的核心业务逻辑
"""
import logging
from typing import Optional, List
from datetime import datetime

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, ConversationStatus, ConversationType
from app.models.turn import Turn, TurnStatus
from app.models.message import Message, MessageRole
from app.repositories.message_repository import MessageRepository

logger = logging.getLogger(__name__)


class ConversationService:
    """
    对话服务

    核心功能:
    1. 创建和管理对话
    2. 发送消息并创建 Turn
    3. 更新 shared_memory
    4. 生成 context_summary
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.message_repo = MessageRepository(db)

    async def create_conversation(
        self,
        workspace_id: str,
        title: Optional[str] = None,
        conversation_type: ConversationType = ConversationType.CHAT,
        initial_message: Optional[str] = None,
    ) -> tuple[Conversation, Optional[Turn]]:
        """
        创建新对话

        Args:
            workspace_id: 工作空间 ID
            title: 对话标题 (可选,不提供则使用默认值)
            conversation_type: 对话类型
            initial_message: 初始消息 (可选)

        Returns:
            (Conversation, Turn): 对话对象和首个 Turn (如果提供了 initial_message)
        """
        # 1. 创建 Conversation
        conversation = Conversation(
            workspace_id=workspace_id,
            title=title or "新对话",
            conversation_type=conversation_type,
            status=ConversationStatus.ACTIVE,
            turn_count=0,
            message_count=0,
            shared_memory={},
        )
        self.db.add(conversation)
        await self.db.flush()  # 获取 conversation.id

        logger.info(
            "conversation_created",
            conversation_id=conversation.id,
            workspace_id=workspace_id,
            conversation_type=conversation_type.value,
        )

        # 2. 如果提供了初始消息,创建首个 Turn
        turn = None
        if initial_message:
            turn = await self.send_message(
                conversation_id=conversation.id,
                content=initial_message,
            )

        await self.db.commit()
        return conversation, turn

    async def send_message(
        self,
        conversation_id: str,
        content: str,
        parent_message_id: Optional[str] = None,
    ) -> Turn:
        """
        向对话发送新消息 (核心方法)

        流程:
        1. 验证 conversation 存在且为 active
        2. 创建新的 Turn
        3. 保存 User Message
        4. 返回 Turn (等待 Agent Worker 执行)

        Args:
            conversation_id: 对话 ID
            content: 消息内容
            parent_message_id: 父消息 ID (用于分支对话)

        Returns:
            Turn: 新创建的 Turn
        """
        # 1. 验证 conversation
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        if conversation.status != ConversationStatus.ACTIVE:
            raise ValueError(f"Conversation {conversation_id} is not active")

        # 2. 创建 Turn
        turn_number = conversation.turn_count + 1
        turn = Turn(
            conversation_id=conversation_id,
            turn_number=turn_number,
            user_input=content,
            status=TurnStatus.PENDING,
        )
        self.db.add(turn)
        await self.db.flush()  # 获取 turn.id

        # 3. 保存 User Message
        user_message = await self.message_repo.create_user_message(
            session_id=None,  # Session 稍后由 Agent Worker 创建
            content=content,
            conversation_id=conversation_id,
            turn_id=turn.id,
        )

        # 4. 更新 Turn 的 user_message_id
        turn.user_message_id = user_message.id

        # 5. 更新 Conversation 统计
        conversation.turn_count = turn_number
        conversation.message_count += 1
        conversation.last_message_at = datetime.utcnow()

        await self.db.commit()

        logger.info(
            "message_sent",
            conversation_id=conversation_id,
            turn_id=turn.id,
            turn_number=turn_number,
            content_length=len(content),
        )

        return turn

    async def get_conversation(
        self,
        conversation_id: str,
        include_turns: bool = False,
        include_messages: bool = False,
    ) -> Optional[Conversation]:
        """
        获取对话详情

        Args:
            conversation_id: 对话 ID
            include_turns: 是否包含 Turns
            include_messages: 是否包含 Messages

        Returns:
            Conversation: 对话对象
        """
        query = select(Conversation).where(Conversation.id == conversation_id)

        if include_turns:
            query = query.options(selectinload(Conversation.turns))
        if include_messages:
            query = query.options(selectinload(Conversation.messages))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_conversations(
        self,
        workspace_id: str,
        status: Optional[ConversationStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Conversation]:
        """
        列出对话列表

        Args:
            workspace_id: 工作空间 ID
            status: 对话状态筛选
            limit: 返回数量
            offset: 偏移量

        Returns:
            List[Conversation]: 对话列表
        """
        query = select(Conversation).where(Conversation.workspace_id == workspace_id)

        if status:
            query = query.where(Conversation.status == status)

        query = query.order_by(desc(Conversation.last_message_at)).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_shared_memory(
        self,
        conversation_id: str,
        memory_update: dict,
        merge: bool = True,
    ):
        """
        更新 shared_memory

        Args:
            conversation_id: 对话 ID
            memory_update: 要更新的记忆内容
            merge: 是否合并 (True) 还是替换 (False)
        """
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        if merge:
            # 合并模式: 深度合并字典
            current_memory = conversation.shared_memory or {}
            updated_memory = self._merge_memory(current_memory, memory_update)
            conversation.shared_memory = updated_memory
        else:
            # 替换模式
            conversation.shared_memory = memory_update

        await self.db.commit()

        logger.info(
            "shared_memory_updated",
            conversation_id=conversation_id,
            merge=merge,
            memory_size=len(str(conversation.shared_memory)),
        )

    def _merge_memory(self, current: dict, update: dict) -> dict:
        """
        深度合并两个 memory 字典

        规则:
        - key_facts: 追加,去重
        - entities: 合并列表
        - topics: 追加,去重
        - context: 覆盖
        """
        merged = current.copy()

        # 合并 key_facts
        if "key_facts" in update:
            current_facts = merged.get("key_facts", [])
            new_facts = update["key_facts"]
            # 去重 (基于 fact 内容)
            existing_fact_texts = {f["fact"] for f in current_facts}
            for fact in new_facts:
                if fact["fact"] not in existing_fact_texts:
                    current_facts.append(fact)
            merged["key_facts"] = current_facts[-50:]  # 保留最近 50 条

        # 合并 entities
        if "entities" in update:
            current_entities = merged.get("entities", {})
            for entity_type, entity_list in update["entities"].items():
                if entity_type not in current_entities:
                    current_entities[entity_type] = []
                # 去重并追加
                existing = set(current_entities[entity_type])
                for entity in entity_list:
                    if entity not in existing:
                        current_entities[entity_type].append(entity)
            merged["entities"] = current_entities

        # 合并 topics
        if "topics" in update:
            current_topics = set(merged.get("topics", []))
            new_topics = set(update["topics"])
            merged["topics"] = list(current_topics | new_topics)

        # 覆盖 context
        if "context" in update:
            merged["context"] = update["context"]

        # 覆盖 user_preferences
        if "user_preferences" in update:
            merged["user_preferences"] = update["user_preferences"]

        return merged

    async def archive_conversation(self, conversation_id: str):
        """归档对话"""
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        conversation.status = ConversationStatus.ARCHIVED
        conversation.archived_at = datetime.utcnow()
        await self.db.commit()

        logger.info("conversation_archived", conversation_id=conversation_id)

    async def get_message_history(
        self,
        conversation_id: str,
        limit: int = 20,
    ) -> List[Message]:
        """
        获取对话的消息历史

        Args:
            conversation_id: 对话 ID
            limit: 返回最近 N 条消息

        Returns:
            List[Message]: 消息列表 (按时间升序)
        """
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(desc(Message.created_at))
            .limit(limit)
        )

        result = await self.db.execute(query)
        messages = list(result.scalars().all())
        return list(reversed(messages))  # 反转为升序
