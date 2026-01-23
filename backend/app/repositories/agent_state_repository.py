import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.datetime_utils import utc_now_naive
from app.models.agent_state import AgentCheckpoint, AgentState


class AgentStateRepository:
    """Repository for AgentState operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        session_id: str,
        agent_config_id: str | None = None,
        current_state: str = "IDLE",
        state_data: dict | None = None
    ) -> AgentState:
        """Create a new agent state"""
        state = AgentState(
            id=str(uuid.uuid4()),
            session_id=session_id,
            agent_config_id=agent_config_id,
            current_state=current_state,
            state_data=state_data or {},
            started_at=utc_now_naive()
        )

        self.db.add(state)
        await self.db.commit()
        await self.db.refresh(state)

        return state

    async def get_by_session(self, session_id: str) -> AgentState | None:
        """Get agent state by session ID"""
        result = await self.db.execute(
            select(AgentState)
            .options(selectinload(AgentState.agent_config))
            .where(AgentState.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def update_state(
        self,
        session_id: str,
        current_state: str,
        iteration_count: int | None = None,
        state_data: dict | None = None
    ) -> AgentState | None:
        """Update agent state"""
        state = await self.get_by_session(session_id)
        if not state:
            return None

        if current_state:
            state.current_state = current_state

        if iteration_count is not None:
            state.iteration_count = iteration_count

        if state_data is not None:
            state.state_data = state_data

        state.last_activity_at = utc_now_naive()

        await self.db.commit()
        await self.db.refresh(state)

        return state

    async def update_token_usage(
        self,
        session_id: str,
        input_tokens: int = 0,
        output_tokens: int = 0
    ) -> AgentState | None:
        """Update token usage"""
        state = await self.get_by_session(session_id)
        if not state:
            return None

        state.input_tokens_used += input_tokens
        state.output_tokens_used += output_tokens
        state.total_tokens_used = state.input_tokens_used + state.output_tokens_used
        state.last_activity_at = utc_now_naive()

        await self.db.commit()
        await self.db.refresh(state)

        return state

    async def update_tool_stats(
        self,
        session_id: str,
        success: bool = True
    ) -> AgentState | None:
        """Update tool call statistics"""
        state = await self.get_by_session(session_id)
        if not state:
            return None

        state.tool_calls_count += 1
        if success:
            state.tool_calls_success += 1
        else:
            state.tool_calls_failed += 1

        state.last_activity_at = utc_now_naive()

        await self.db.commit()
        await self.db.refresh(state)

        return state

    async def record_error(
        self,
        session_id: str,
        error_message: str
    ) -> AgentState | None:
        """Record an error"""
        state = await self.get_by_session(session_id)
        if not state:
            return None

        state.error_count += 1
        state.last_error = error_message
        state.last_error_time = utc_now_naive()
        state.last_activity_at = utc_now_naive()

        await self.db.commit()
        await self.db.refresh(state)

        return state

    async def complete_session(
        self,
        session_id: str,
        total_execution_time: float | None = None
    ) -> AgentState | None:
        """Mark session as completed"""
        state = await self.get_by_session(session_id)
        if not state:
            return None

        state.current_state = "COMPLETED"
        state.completed_at = utc_now_naive()

        if total_execution_time is not None:
            state.total_execution_time = total_execution_time

            if state.iteration_count > 0:
                state.average_iteration_time = total_execution_time / state.iteration_count

        state.last_activity_at = utc_now_naive()

        await self.db.commit()
        await self.db.refresh(state)

        return state

    async def delete(self, session_id: str) -> bool:
        """Delete agent state for a session"""
        state = await self.get_by_session(session_id)
        if not state:
            return False

        await self.db.delete(state)
        await self.db.commit()

        return True


class AgentCheckpointRepository:
    """Repository for AgentCheckpoint operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        agent_state_id: str,
        iteration: int,
        checkpoint_type: str,
        context_snapshot: dict | None = None,
        working_memory_snapshot: dict | None = None,
        reason: str | None = None,
        metadata: dict | None = None
    ) -> AgentCheckpoint:
        """Create a new checkpoint"""
        checkpoint = AgentCheckpoint(
            id=str(uuid.uuid4()),
            agent_state_id=agent_state_id,
            iteration=iteration,
            checkpoint_type=checkpoint_type,
            context_snapshot=context_snapshot,
            working_memory_snapshot=working_memory_snapshot,
            reason=reason,
            metadata=metadata or {}
        )

        self.db.add(checkpoint)
        await self.db.commit()
        await self.db.refresh(checkpoint)

        return checkpoint

    async def get_by_agent_state(
        self,
        agent_state_id: str,
        limit: int = 10
    ) -> list[AgentCheckpoint]:
        """Get checkpoints for an agent state"""
        result = await self.db.execute(
            select(AgentCheckpoint)
            .where(AgentCheckpoint.agent_state_id == agent_state_id)
            .order_by(AgentCheckpoint.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest(
        self,
        agent_state_id: str,
        checkpoint_type: str | None = None
    ) -> AgentCheckpoint | None:
        """Get latest checkpoint"""
        query = select(AgentCheckpoint).where(
            AgentCheckpoint.agent_state_id == agent_state_id
        )

        if checkpoint_type:
            query = query.where(AgentCheckpoint.checkpoint_type == checkpoint_type)

        result = await self.db.execute(
            query.order_by(AgentCheckpoint.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def delete_old_checkpoints(
        self,
        agent_state_id: str,
        keep_last_n: int = 5
    ) -> int:
        """Delete old checkpoints, keeping only the last N"""
        result = await self.db.execute(
            select(AgentCheckpoint.id)
            .where(AgentCheckpoint.agent_state_id == agent_state_id)
            .order_by(AgentCheckpoint.created_at.desc())
        .offset(keep_last_n)
        )
        old_checkpoint_ids = [row[0] for row in result.all()]

        if not old_checkpoint_ids:
            return 0

        for checkpoint_id in old_checkpoint_ids:
            await self.db.execute(
                select(AgentCheckpoint).where(AgentCheckpoint.id == checkpoint_id)
            )

        await self.db.commit()

        return len(old_checkpoint_ids)
