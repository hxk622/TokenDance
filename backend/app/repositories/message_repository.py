"""
Message repository - database access layer for messages.
"""
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message, MessageRole


class MessageRepository:
    """Repository for Message database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        session_id: str | None,
        role: MessageRole,
        content: str | None = None,
        thinking: str | None = None,
        tool_calls: list[dict] | None = None,
        tool_call_id: str | None = None,
        citations: list[dict] | None = None,
        tokens_used: int = 0,
        full_result_ref: str | None = None,
        conversation_id: str | None = None,
        turn_id: str | None = None,
    ) -> Message:
        """Create a new message."""
        message = Message(
            id=str(uuid4()),
            session_id=session_id,
            conversation_id=conversation_id,
            turn_id=turn_id,
            role=role,
            content=content,
            thinking=thinking,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            citations=citations,
            tokens_used=tokens_used,
            full_result_ref=full_result_ref,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def create_user_message(
        self,
        session_id: str | None,
        content: str,
        conversation_id: str | None = None,
        turn_id: str | None = None,
    ) -> Message:
        """Create a user message."""
        return await self.create(
            session_id=session_id,
            role=MessageRole.USER,
            content=content,
            conversation_id=conversation_id,
            turn_id=turn_id,
        )

    async def create_assistant_message(
        self,
        session_id: str | None,
        content: str | None = None,
        thinking: str | None = None,
        tool_calls: list[dict] | None = None,
        citations: list[dict] | None = None,
        tokens_used: int = 0,
        conversation_id: str | None = None,
        turn_id: str | None = None,
    ) -> Message:
        """Create an assistant message."""
        return await self.create(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=content,
            thinking=thinking,
            tool_calls=tool_calls,
            citations=citations,
            tokens_used=tokens_used,
            conversation_id=conversation_id,
            turn_id=turn_id,
        )

    async def create_tool_message(
        self,
        session_id: str | None,
        tool_call_id: str,
        content: str,
        full_result_ref: str | None = None,
        conversation_id: str | None = None,
        turn_id: str | None = None,
    ) -> Message:
        """Create a tool response message."""
        return await self.create(
            session_id=session_id,
            role=MessageRole.TOOL,
            content=content,
            tool_call_id=tool_call_id,
            full_result_ref=full_result_ref,
            conversation_id=conversation_id,
            turn_id=turn_id,
        )

    async def get_by_id(self, message_id: str) -> Message | None:
        """Get message by ID."""
        query = select(Message).where(Message.id == message_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_session(
        self,
        session_id: str,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Message]:
        """
        Get messages by session in chronological order.
        """
        query = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
            .offset(offset)
        )

        if limit:
            query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_recent_messages(
        self,
        session_id: str,
        limit: int = 10,
    ) -> list[Message]:
        """Get the most recent N messages in a session."""
        query = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        messages = list(result.scalars().all())
        return list(reversed(messages))  # Return in chronological order

    async def get_conversation_history(
        self,
        session_id: str,
        max_tokens: int | None = None,
    ) -> list[Message]:
        """
        Get conversation history for context building.
        If max_tokens is specified, return messages that fit within token budget.
        """
        messages = await self.get_by_session(session_id)

        if not max_tokens:
            return messages

        # Calculate from most recent to oldest
        selected = []
        total_tokens = 0

        for message in reversed(messages):
            if total_tokens + message.tokens_used > max_tokens:
                break
            selected.insert(0, message)
            total_tokens += message.tokens_used

        return selected

    async def get_failed_tool_calls(
        self,
        session_id: str,
    ) -> list[dict]:
        """
        Get all failed tool calls from assistant messages (for Keep the Failures).
        """
        messages = await self.get_by_session(session_id)

        failed_calls = []
        for message in messages:
            if message.role == MessageRole.ASSISTANT and message.tool_calls:
                for tool_call in message.tool_calls:
                    if tool_call.get("status") in ("error", "failed"):
                        failed_calls.append({
                            "message_id": message.id,
                            "tool_call": tool_call,
                            "timestamp": message.created_at,
                        })

        return failed_calls

    async def update(
        self,
        message_id: str,
        **updates,
    ) -> Message | None:
        """Update message fields.

        Note: To explicitly set a field to None, include it in updates.
        Fields not in updates will not be modified.
        """
        message = await self.get_by_id(message_id)
        if not message:
            return None

        for key, value in updates.items():
            if hasattr(message, key):
                # Allow setting to None explicitly (e.g., clearing feedback)
                setattr(message, key, value)

        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def delete(self, message_id: str) -> bool:
        """Delete a message."""
        message = await self.get_by_id(message_id)
        if not message:
            return False

        await self.db.delete(message)
        await self.db.commit()
        return True

    async def delete_by_session(self, session_id: str) -> int:
        """Delete all messages in a session. Returns count of deleted messages."""
        messages = await self.get_by_session(session_id)
        count = len(messages)

        for message in messages:
            await self.db.delete(message)

        await self.db.commit()
        return count

    def to_llm_format(self, messages: list[Message]) -> list[dict]:
        """Convert messages to LLM-compatible format."""
        return [msg.to_llm_format() for msg in messages]
