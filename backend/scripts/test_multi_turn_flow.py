"""
Test Multi-Turn Conversation Flow

This script tests the complete multi-turn conversation implementation:
1. Create a conversation
2. Send initial message
3. Wait for Agent to complete
4. Send follow-up message
5. Verify shared_memory is preserved

Usage:
    cd backend
    uv run python scripts/test_multi_turn_flow.py
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import async_session_maker, init_db
from app.core.logging import get_logger, setup_logging
from app.models.conversation import ConversationType
from app.services.conversation_service import ConversationService

logger = get_logger(__name__)


async def test_multi_turn_flow():
    """Test complete multi-turn conversation flow."""
    setup_logging()

    logger.info("=== Starting Multi-Turn Conversation Test ===")

    # Initialize database
    await init_db()

    async with async_session_maker() as db:
        service = ConversationService(db)

        # Step 1: Create test workspace (assuming workspace exists)
        # In production, you'd get this from the user's workspace
        workspace_id = "test_workspace_id"  # Replace with actual workspace ID

        logger.info("Step 1: Creating conversation...")
        conversation, turn1 = await service.create_conversation(
            workspace_id=workspace_id,
            title="Multi-Turn Test Conversation",
            conversation_type=ConversationType.RESEARCH,
            initial_message="帮我调研 AI Agent 市场",
        )

        logger.info(
            "conversation_created",
            conversation_id=conversation.id,
            turn_id=turn1.id if turn1 else None,
            turn_count=conversation.turn_count,
        )

        # Step 2: Simulate Agent completion (in real flow, Agent Worker does this)
        if turn1:
            logger.info("Step 2: Simulating Agent completion...")
            turn1.start()
            await db.commit()

            # Simulate Agent response
            turn1.complete("msg_assistant_1", tokens_used=1000)
            turn1.assistant_response = "好的,我来帮你调研 AI Agent 市场..."
            await db.commit()

            # Update shared_memory
            await service.update_shared_memory(
                conversation.id,
                {
                    "key_facts": [
                        {
                            "fact": "AI Agent 是当前热门领域",
                            "source": "turn_1",
                            "confidence": 0.9,
                        }
                    ],
                    "topics": ["AI Agent", "市场调研"],
                },
                merge=True,
            )

            logger.info("turn_1_completed", tokens_used=1000)

        # Step 3: Send follow-up message
        logger.info("Step 3: Sending follow-up message...")
        turn2 = await service.send_message(
            conversation_id=conversation.id,
            content="市场规模是多少?",
        )

        logger.info(
            "turn_2_created",
            turn_id=turn2.id,
            turn_number=turn2.turn_number,
        )

        # Step 4: Verify conversation state
        logger.info("Step 4: Verifying conversation state...")
        updated_conversation = await service.get_conversation(
            conversation.id,
            include_turns=True,
        )

        assert updated_conversation.turn_count == 2, f"Expected 2 turns, got {updated_conversation.turn_count}"
        assert len(updated_conversation.turns) == 2, f"Expected 2 turns in list, got {len(updated_conversation.turns)}"

        # Verify shared_memory
        memory = updated_conversation.shared_memory
        assert memory is not None, "shared_memory should not be None"
        assert "key_facts" in memory, "key_facts should be in shared_memory"
        assert "topics" in memory, "topics should be in shared_memory"
        assert len(memory["key_facts"]) == 1, f"Expected 1 fact, got {len(memory['key_facts'])}"
        assert set(memory["topics"]) == {"AI Agent", "市场调研"}, f"Unexpected topics: {memory['topics']}"

        logger.info(
            "conversation_verified",
            turn_count=updated_conversation.turn_count,
            message_count=updated_conversation.message_count,
            shared_memory_keys=list(memory.keys()),
        )

        # Step 5: Test message history
        logger.info("Step 5: Testing message history...")
        message_history = await service.get_message_history(conversation.id, limit=10)

        logger.info(
            "message_history_retrieved",
            count=len(message_history),
            messages=[msg.content[:50] for msg in message_history],
        )

        logger.info("=== Multi-Turn Conversation Test PASSED ===")

        return {
            "conversation_id": conversation.id,
            "turn_count": updated_conversation.turn_count,
            "message_count": updated_conversation.message_count,
            "shared_memory": memory,
        }


async def main():
    """Main entry point."""
    try:
        result = await test_multi_turn_flow()
        print("\n✅ Test completed successfully!")
        print(f"Conversation ID: {result['conversation_id']}")
        print(f"Turn count: {result['turn_count']}")
        print(f"Message count: {result['message_count']}")
        print(f"Shared memory keys: {list(result['shared_memory'].keys())}")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test error: {e}", exc_info=True)
        print(f"\n❌ Test error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
