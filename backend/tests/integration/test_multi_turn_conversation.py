"""
Integration Tests for Multi-Turn Conversation

测试完整的多轮对话流程
"""
import pytest
import asyncio
from datetime import datetime

from app.models.conversation import Conversation, ConversationStatus, ConversationType
from app.models.turn import Turn, TurnStatus
from app.models.message import Message, MessageRole
from app.services.conversation_service import ConversationService


@pytest.mark.asyncio
class TestMultiTurnConversationFlow:
    """测试完整的多轮对话流程"""

    async def test_complete_multi_turn_conversation(
        self, db_session, test_workspace
    ):
        """
        测试完整的多轮对话流程

        场景:
        1. 用户: "帮我调研 AI Agent 市场"
        2. Agent: "好的,我来帮你调研..."
        3. 用户: "市场规模是多少?"
        4. Agent: "根据调研,2024年约50亿美元..."
        5. 用户: "帮我确认下这个数据"
        6. Agent: "正在确认..."
        """
        service = ConversationService(db_session)

        # Turn 1: 创建对话并发送首条消息
        conversation, turn1 = await service.create_conversation(
            workspace_id=test_workspace.id,
            title="AI Agent 市场调研",
            conversation_type=ConversationType.RESEARCH,
            initial_message="帮我调研 AI Agent 市场",
        )

        assert conversation.id is not None
        assert conversation.turn_count == 1
        assert turn1.turn_number == 1
        assert turn1.user_input == "帮我调研 AI Agent 市场"

        # 模拟 Agent 完成执行
        turn1.complete("msg_assistant_1", tokens_used=1000)
        turn1.assistant_response = "好的,我来帮你调研 AI Agent 市场..."
        await db_session.commit()

        # 更新 shared_memory
        await service.update_shared_memory(
            conversation.id,
            {
                "key_facts": [
                    {"fact": "AI Agent 是当前热门领域", "source": "turn_1", "confidence": 0.9}
                ],
                "topics": ["AI Agent", "市场调研"],
            },
            merge=True,
        )

        # Turn 2: 发送追问消息
        turn2 = await service.send_message(
            conversation_id=conversation.id,
            content="市场规模是多少?",
        )

        assert turn2.turn_number == 2
        assert turn2.user_input == "市场规模是多少?"

        # 模拟 Agent 完成执行
        turn2.complete("msg_assistant_2", tokens_used=800)
        turn2.assistant_response = "根据调研,2024年全球 AI Agent 市场规模约50亿美元..."
        await db_session.commit()

        # 更新 shared_memory
        await service.update_shared_memory(
            conversation.id,
            {
                "key_facts": [
                    {"fact": "2024年全球 AI Agent 市场规模约50亿美元", "source": "turn_2", "confidence": 0.9}
                ],
                "topics": ["市场规模"],
            },
            merge=True,
        )

        # Turn 3: 再次追问
        turn3 = await service.send_message(
            conversation_id=conversation.id,
            content="帮我确认下这个数据",
        )

        assert turn3.turn_number == 3

        # 验证 Conversation 状态
        updated_conversation = await service.get_conversation(conversation.id, include_turns=True)
        assert updated_conversation.turn_count == 3
        assert updated_conversation.message_count == 3  # 3 user messages
        assert len(updated_conversation.turns) == 3

        # 验证 shared_memory 合并正确
        memory = updated_conversation.shared_memory
        assert len(memory["key_facts"]) == 2
        assert set(memory["topics"]) == {"AI Agent", "市场调研", "市场规模"}

    async def test_conversation_context_preservation(
        self, db_session, test_workspace
    ):
        """
        测试对话上下文保持

        验证:
        1. shared_memory 在多轮对话中累积
        2. 历史消息可以被检索
        3. Turn 之间的关联正确
        """
        service = ConversationService(db_session)

        # 创建对话
        conversation, _ = await service.create_conversation(
            workspace_id=test_workspace.id,
            title="Context Test",
        )

        # 发送 5 条消息
        for i in range(5):
            turn = await service.send_message(
                conversation_id=conversation.id,
                content=f"Message {i}",
            )

            # 模拟完成
            turn.complete(f"msg_assistant_{i}", tokens_used=100)
            await db_session.commit()

            # 每次更新 shared_memory
            await service.update_shared_memory(
                conversation.id,
                {
                    "key_facts": [
                        {"fact": f"Fact from turn {i}", "source": f"turn_{i}", "confidence": 0.9}
                    ],
                },
                merge=True,
            )

        # 验证上下文
        updated_conversation = await service.get_conversation(conversation.id)
        assert updated_conversation.turn_count == 5

        # 验证 shared_memory 累积
        memory = updated_conversation.shared_memory
        assert len(memory["key_facts"]) == 5

        # 验证历史消息
        message_history = await service.get_message_history(conversation.id, limit=10)
        assert len(message_history) == 5

    async def test_concurrent_turns_handling(
        self, db_session, test_workspace
    ):
        """
        测试并发 Turn 处理

        验证:
        1. turn_number 正确递增
        2. 不会出现重复的 turn_number
        """
        service = ConversationService(db_session)

        # 创建对话
        conversation, _ = await service.create_conversation(
            workspace_id=test_workspace.id,
            title="Concurrent Test",
        )

        # 并发发送 3 条消息
        tasks = [
            service.send_message(conversation.id, f"Concurrent message {i}")
            for i in range(3)
        ]
        turns = await asyncio.gather(*tasks)

        # 验证 turn_number 唯一且递增
        turn_numbers = [turn.turn_number for turn in turns]
        assert len(set(turn_numbers)) == 3  # 无重复
        assert sorted(turn_numbers) == [1, 2, 3]

    async def test_shared_memory_size_limit(
        self, db_session, test_workspace
    ):
        """
        测试 shared_memory 大小限制

        验证:
        1. key_facts 限制为 50 条
        2. 旧的 facts 被移除
        """
        service = ConversationService(db_session)

        conversation, _ = await service.create_conversation(
            workspace_id=test_workspace.id,
            title="Memory Limit Test",
        )

        # 添加 60 条 facts
        for i in range(6):
            facts = [
                {"fact": f"Fact {i * 10 + j}", "source": "test", "confidence": 0.9}
                for j in range(10)
            ]
            await service.update_shared_memory(
                conversation.id,
                {"key_facts": facts},
                merge=True,
            )

        # 验证只保留最近 50 条
        updated_conversation = await service.get_conversation(conversation.id)
        memory = updated_conversation.shared_memory
        assert len(memory["key_facts"]) == 50
        assert memory["key_facts"][-1]["fact"] == "Fact 59"  # 最新的

    async def test_conversation_archival(
        self, db_session, test_workspace
    ):
        """
        测试对话归档

        验证:
        1. 归档后状态变为 ARCHIVED
        2. 归档后不能发送新消息
        """
        service = ConversationService(db_session)

        # 创建对话
        conversation, _ = await service.create_conversation(
            workspace_id=test_workspace.id,
            title="Archive Test",
        )

        # 发送一条消息
        await service.send_message(conversation.id, "Test message")

        # 归档
        await service.archive_conversation(conversation.id)

        # 验证状态
        updated_conversation = await service.get_conversation(conversation.id)
        assert updated_conversation.status == ConversationStatus.ARCHIVED
        assert updated_conversation.archived_at is not None

        # 尝试发送消息应该失败
        with pytest.raises(ValueError, match="is not active"):
            await service.send_message(conversation.id, "This should fail")


@pytest.mark.asyncio
class TestSharedMemoryManagement:
    """测试 shared_memory 管理"""

    async def test_memory_merge_deduplication(
        self, db_session, test_workspace
    ):
        """测试记忆合并和去重"""
        service = ConversationService(db_session)

        conversation, _ = await service.create_conversation(
            workspace_id=test_workspace.id,
            title="Dedup Test",
        )

        # 添加重复的 facts
        await service.update_shared_memory(
            conversation.id,
            {
                "key_facts": [
                    {"fact": "AI Agent 市场规模 50 亿", "source": "turn_1", "confidence": 0.9}
                ],
            },
            merge=True,
        )

        await service.update_shared_memory(
            conversation.id,
            {
                "key_facts": [
                    {"fact": "AI Agent 市场规模 50 亿", "source": "turn_2", "confidence": 0.95}  # 重复
                ],
            },
            merge=True,
        )

        # 验证去重
        updated_conversation = await service.get_conversation(conversation.id)
        memory = updated_conversation.shared_memory
        assert len(memory["key_facts"]) == 1

    async def test_memory_entities_merge(
        self, db_session, test_workspace
    ):
        """测试实体合并"""
        service = ConversationService(db_session)

        conversation, _ = await service.create_conversation(
            workspace_id=test_workspace.id,
            title="Entities Test",
        )

        # 第一次添加
        await service.update_shared_memory(
            conversation.id,
            {
                "entities": {
                    "companies": ["OpenAI", "Anthropic"],
                    "products": ["ChatGPT"],
                }
            },
            merge=True,
        )

        # 第二次添加
        await service.update_shared_memory(
            conversation.id,
            {
                "entities": {
                    "companies": ["Google"],  # 新公司
                    "products": ["Claude", "ChatGPT"],  # 新产品 + 重复
                }
            },
            merge=True,
        )

        # 验证合并
        updated_conversation = await service.get_conversation(conversation.id)
        memory = updated_conversation.shared_memory

        assert set(memory["entities"]["companies"]) == {"OpenAI", "Anthropic", "Google"}
        assert set(memory["entities"]["products"]) == {"ChatGPT", "Claude"}


@pytest.mark.asyncio
class TestMessageHistory:
    """测试消息历史"""

    async def test_message_history_ordering(
        self, db_session, test_workspace
    ):
        """测试消息历史排序"""
        service = ConversationService(db_session)

        conversation, _ = await service.create_conversation(
            workspace_id=test_workspace.id,
            title="History Test",
        )

        # 发送 5 条消息
        for i in range(5):
            await service.send_message(conversation.id, f"Message {i}")
            await asyncio.sleep(0.01)  # 确保时间戳不同

        # 获取历史 (升序)
        history = await service.get_message_history(conversation.id, limit=10)

        # 验证顺序
        assert len(history) == 5
        for i, msg in enumerate(history):
            assert msg.content == f"Message {i}"

    async def test_message_history_limit(
        self, db_session, test_workspace
    ):
        """测试消息历史限制"""
        service = ConversationService(db_session)

        conversation, _ = await service.create_conversation(
            workspace_id=test_workspace.id,
            title="Limit Test",
        )

        # 发送 20 条消息
        for i in range(20):
            await service.send_message(conversation.id, f"Message {i}")

        # 只获取最近 5 条
        history = await service.get_message_history(conversation.id, limit=5)

        assert len(history) == 5
        assert history[0].content == "Message 15"  # 最早的
        assert history[-1].content == "Message 19"  # 最新的


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
