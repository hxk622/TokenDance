"""
Tests for Conversation Service

测试多轮对话的核心业务逻辑
"""
import pytest
from datetime import datetime

from app.models.conversation import Conversation, ConversationStatus, ConversationType
from app.models.turn import Turn, TurnStatus
from app.models.message import Message, MessageRole
from app.services.conversation_service import ConversationService


@pytest.fixture
async def conversation_service(db_session):
    """创建 ConversationService 实例"""
    return ConversationService(db_session)


@pytest.fixture
async def test_workspace(db_session):
    """创建测试工作空间"""
    from app.models.workspace import Workspace
    workspace = Workspace(
        id="test_workspace_123",
        name="Test Workspace",
        owner_id="test_user_123",
    )
    db_session.add(workspace)
    await db_session.commit()
    return workspace


class TestConversationCreation:
    """测试对话创建"""

    async def test_create_conversation_without_initial_message(
        self, conversation_service, test_workspace
    ):
        """测试创建对话 (不带初始消息)"""
        # Act
        conversation, turn = await conversation_service.create_conversation(
            workspace_id=test_workspace.id,
            title="Test Conversation",
            conversation_type=ConversationType.RESEARCH,
        )

        # Assert
        assert conversation.id is not None
        assert conversation.workspace_id == test_workspace.id
        assert conversation.title == "Test Conversation"
        assert conversation.conversation_type == ConversationType.RESEARCH
        assert conversation.status == ConversationStatus.ACTIVE
        assert conversation.turn_count == 0
        assert conversation.message_count == 0
        assert conversation.shared_memory == {}
        assert turn is None  # 没有初始消息,不创建 Turn

    async def test_create_conversation_with_initial_message(
        self, conversation_service, test_workspace
    ):
        """测试创建对话 (带初始消息)"""
        # Act
        conversation, turn = await conversation_service.create_conversation(
            workspace_id=test_workspace.id,
            title="Research AI Agent",
            conversation_type=ConversationType.RESEARCH,
            initial_message="帮我调研下 AI Agent 市场",
        )

        # Assert
        assert conversation.id is not None
        assert conversation.turn_count == 1
        assert conversation.message_count == 1
        assert turn is not None
        assert turn.turn_number == 1
        assert turn.user_input == "帮我调研下 AI Agent 市场"
        assert turn.status == TurnStatus.PENDING


class TestSendMessage:
    """测试发送消息"""

    async def test_send_message_creates_turn(
        self, conversation_service, test_workspace
    ):
        """测试发送消息创建 Turn"""
        # Arrange
        conversation, _ = await conversation_service.create_conversation(
            workspace_id=test_workspace.id,
            title="Test",
        )

        # Act
        turn = await conversation_service.send_message(
            conversation_id=conversation.id,
            content="Hello, Agent!",
        )

        # Assert
        id is not None
        assert turn.conversation_id == conversation.id
        assert turn.turn_number == 1
        assert turn.user_input == "Hello, Agent!"
        assert turn.status == TurnStatus.PENDING
        assert turn.user_message_id is not None

        # 验证 Conversation 更新
        updated_conversation = await conversation_service.get_conversation(conversation.id)
        assert updated_conversation.turn_count == 1
        assert updated_conversation.message_count == 1
        assert updated_conversation.last_message_at is not None

    async def test_send_multiple_messages(
        self, conversation_service, test_workspace
    ):
        """测试发送多条消息"""
        # Arrange
        conversation, _ = await conversation_service.create_conversation(
            workspace_id=test_workspace.id,
            title="Multi-turn Test",
        )

        # Act - 发送 3 条消息
        turn1 = await conversation_service.send_message(
            conversation_id=conversation.id,
            content="First message",
        )
        turn2 = await conversation_service.send_message(
            conversation_id=conversation.id,
            content="Second message",
        )
        turn3 = await conversation_service.send_message(
            conversation_id=conversation.id,
            content="Third message",
        )

        # Assert
        assert turn1.turn_number == 1
        assert turn2.turn_number == 2
        assert turn3.turn_number == 3

        updated_conversation = await conversation_service.get_conversation(conversation.id)
        assert updated_conversation.turn_count == 3
        assert updated_conversation.message_count == 3

    async def test_send_message_to_archived_conversation_fails(
        self, conversation_service, test_workspace
    ):
        """测试向已归档的对话发送消息失败"""
        # Arrange
        conversation, _ = await conversation_service.create_conversation(
            workspace_id=test_workspace.id,
            title="Test",
        )
        await conversation_service.archive_conversation(conversation.id)

        # Act & Assert
        with pytest.raises(ValueError, match="is not active"):
            await conversation_service.send_message(
                conversation_id=conversation.id,
                content="This should fail",
            )


class TestSharedMemory:
    """测试 shared_memory 管理"""

    async def test_update_shared_memory_merge_mode(
        self, conversation_service, test_workspace
    ):
        """测试合并模式更新 shared_memory"""
        # Arrange
        conversation, _ = await conversation_service.create_conversation(
            workspace_id=test_workspace.id,
            title="Test",
        )

        # Act - 第一次更新
        await conversation_service.update_shared_memory(
            conversation_id=conversation.id,
            memory_update={
                "key_facts": [
                    {"fact": "AI Agent 市场规模 50 亿美元", "source": "turn_1", "confidence": 0.9}
                ],
                "topics": ["AI Agent", "市场规模"],
            },
            merge=True,
        )

        # Act - 第二次更新 (合并)
        await conversation_service.update_shared_memory(
            conversation_id=conversation.id,
            memory_update={
                "key_facts": [
                    {"fact": "预计 2025 年增长到 100 亿美元", "source": "turn_2", "confidence": 0.8}
                ],
                "topics": ["增长预测"],
                "entities": {"companies": ["OpenAI", "Anthropic"]},
            },
            merge=True,
        )

        # Assert
        updated_conversation = await conversation_service.get_conversation(conversation.id)
        memory = updated_conversation.shared_memory

        assert len(memory["key_facts"]) == 2
        assert set(memory["topics"]) == {"AI Agent", "市场规模", "增长预测"}
        assert memory["entities"]["companies"] == ["OpenAI", "Anthropic"]

    async def test_update_shared_memory_replace_mode(
        self, conversation_service, test_workspace
    ):
        """测试替换模式更新 shared_memory"""
        # Arrange
        conversation, _ = await conversation_service.create_conversation(
            workspace_id=test_workspace.id,
            title="Test",
        )
        await conversation_service.update_shared_memory(
            conversation_id=conversation.id,
            memory_update={"old_data": "should be replaced"},
            merge=False,
        )

        # Act
        await conversation_service.update_shared_memory(
            conversation_id=conversation.id,
            memory_update={"new_data": "replaced"},
            merge=False,
        )

        # Assert
        updated_conversation = await conversation_service.get_conversation(conversation.id)
        memory = updated_conversation.shared_memory

        assert "old_data" not in memory
        assert memory["new_data"] == "replaced"

    async def test_merge_memory_deduplicates_key_facts(
        self, conversation_service, test_workspace
    ):
        """测试 key_facts 去重"""
        # Arrange
        conversation, _ = await conversation_service.create_conversation(
            workspace_id=test_workspace.id,
            title="Test",
        )

        # Act - 添加重复的 fact
        await conversation_service.update_shared_memory(
            conversation_id=conversation.id,
            memory_update={
                "key_facts": [
                    {"fact": "AI Agent 市场规模 50 亿美元", "source": "turn_1", "confidence": 0.9}
                ],
            },
            merge=True,
        )
        await conversation_service.update_shared_memory(
            conversation_id=conversation.id,
            memory_update={
                "key_facts": [
                    {"fact": "AI Agent 市场规模 50 亿美元", "source": "turn_2", "confidence": 0.95}  # 重复
                ],
            },
            merge=True,
        )

        # Assert
        updated_conversation = await conversation_service.get_conversation(conversation.id)
        memory = updated_conversation.shared_memory

        # 应该只有一条 (去重)
        assert len(memory["key_facts"]) == 1

    async def test_merge_memory_limits_key_facts_to_50(
        self, conversation_service, test_workspace
    ):
        """测试 key_facts 限制为 50 条"""
        # Arrange
        conversation, _ = await conversation_service.create_conversation(
            workspace_id=test_workspace.id,
            title="Test",
        )

        # Act - 添加 60 条 facts
        facts = [
            {"fact": f"Fact {i}", "source": "test", "confidence": 0.9}
            for i in range(60)
        ]
        await conversation_service.update_shared_memory(
            conversation_id=conversation.id,
            memory_update={"key_facts": facts},
            merge=True,
        )

        # Assert
        updated_conversation = await conversation_service.get_conversation(conversation.id)
        memory = updated_conversation.shared_memory

        # 应该只保留最近 50 条
        assert len(memory["key_facts"]) == 50
        assert memory["key_facts"][-1]["fact"] == "Fact 59"  # 最新的


class TestGetMessageHistory:
    """测试获取消息历史"""

    async def test_get_message_history_returns_recent_messages(
        self, conversation_service, test_workspace, db_session
    ):
        """测试获取最近的消息历史"""
        # Arrange
        conversation, _ = await conversation_service.create_conversation(
            workspace_id=test_workspace.id,
            title="Test",
        )

        # 创建 10 条消息
        for i in range(10):
            turn = await conversation_service.send_message(
                conversation_id=conversation.id,
                content=f"Message {i}",
            )

        # Act
        messages = await conversation_service.get_message_history(
            conversation_id=conversation.id,
            limit=5,
        )

        # Assert
        assert len(messages) == 5
        # 应该是最近的 5 条,按时间升序
        assert messages[0].content == "Message 5"
        assert messages[-1].content == "Message 9"

    async def test_get_message_history_ascending_order(
        self, conversation_service, test_workspace
    ):
        """测试消息历史按时间升序返回"""
        # Arrange
        conversation, _ = await conversation_service.create_conversation(
            workspace_id=test_workspace.id,
            title="Test",
        )

        turn1 = await conversation_service.send_message(
            conversation_id=conversation.id,
            content="First",
        )
        turn2 = await conversation_service.send_message(
            conversation_id=conversation.id,
            content="Second",
        )
        turn3 = await conversation_service.send_message(
            conversation_id=conversation.id,
            content="Third",
        )

        # Act
        messages = await conversation_service.get_message_history(
            conversation_id=conversation.id,
            limit=10,
        )

        # Assert
        assert len(messages) == 3
        assert messages[0].content == "First"
        assert messages[1].content == "Second"
        assert messages[2].content == "Third"


class TestListConversations:
    """测试列出对话列表"""

    async def test_list_conversations_by_workspace(
        self, conversation_service, test_workspace
    ):
        """测试按工作空间列出对话"""
        # Arrange - 创建 3 个对话
        conv1, _ = await conversation_service.create_conversation(
            workspace_id=test_workspace.id,
            title="Conversation 1",
        )
        conv2, _ = await conversation_service.create_conversation(
            workspace_id=test_workspace.id,
            title="Conversation 2",
        )
        conv3, _ = await conversation_service.create_conversation(
            workspace_id=test_workspace.id,
            title="Conversation 3",
        )

        # Act
        conversations = await conversation_service.list_conversations(
            workspace_id=test_workspace.id,
            limit=10,
        )

        # Assert
        assert len(conversations) == 3
        assert {c.id for c in conversations} == {conv1.id, conv2.id, conv3.id}

    async def test_list_conversations_filters_by_status(
        self, conversation_service, test_workspace
    ):
        """测试按状态筛选对话"""
        # Arrange
        conv1, _ = await conversation_service.create_conversation(
            workspace_id=test_workspace.id,
            title="Active",
        )
        conv2, _ = await conversation_service.create_conversation(
            workspace_id=test_workspace.id,
            title="To Archive",
        )
        await conversation_service.archive_conversation(conv2.id)

        # Act - 只获取 active 的
        active_conversations = await conversation_service.list_conversations(
            workspace_id=test_workspace.id,
            status=ConversationStatus.ACTIVE,
        )

        # Assert
        assert len(active_conversations) == 1
        assert active_conversations[0].id == conv1.id

    async def test_list_conversations_ordered_by_last_message(
        self, conversation_service, test_workspace
    ):
        """测试对话按最后消息时间排序"""
        # Arrange
        conv1, _ = await conversation_service.create_conversation(
            workspace_id=test_workspace.id,
            title="Old",
        )
        conv2, _ = await conversation_service.create_conversation(
            workspace_id=test_workspace.id,
            title="New",
        )

        # 向 conv2 发送消息 (更新 last_message_at)
        await conversation_service.send_message(
            conversation_id=conv2.id,
            content="Latest message",
        )

        # Act
        conversations = await conversation_service.list_conversations(
            workspace_id=test_workspace.id,
        )

        # Assert
        # conv2 应该排在前面 (最近有消息)
        assert conversations[0].id == conv2.id
        assert conversations[1].id == conv1.id


class TestArchiveConversation:
    """测试归档对话"""

    async def test_archive_conversation(
        self, conversation_service, test_workspace
    ):
        """测试归档对话"""
        # Arrange
        conversation, _ = await conversation_service.create_conversation(
            workspace_id=test_workspace.id,
            title="Test",
        )

        # Act
        await conversation_service.archive_conversation(conversation.id)

        # Assert
        updated_conversation = await conversation_service.get_conversation(conversation.id)
        assert updated_conversation.status == ConversationStatus.ARCHIVED
        assert updated_conversation.archived_at is not None


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
