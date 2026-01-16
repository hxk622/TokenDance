from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.repositories.agent_state_repository import (
    AgentStateRepository,
    AgentCheckpointRepository
)
from app.models.agent_state import AgentState
from app.agent.working_memory.three_files import ThreeFilesManager
from app.filesystem import AgentFileSystem


class AgentStateService:
    """Service for managing Agent state persistence"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.state_repo = AgentStateRepository(db)
        self.checkpoint_repo = AgentCheckpointRepository(db)
    
    async def initialize_state(
        self,
        session_id: str,
        agent_config_id: Optional[str] = None
    ) -> AgentState:
        """Initialize agent state for a session"""
        
        # Check if state already exists
        existing_state = await self.state_repo.get_by_session(session_id)
        if existing_state:
            return existing_state
        
        # Create new state
        state = await self.state_repo.create(
            session_id=session_id,
            agent_config_id=agent_config_id,
            current_state="IDLE"
        )
        
        return state
    
    async def update_execution_state(
        self,
        session_id: str,
        current_state: str,
        iteration: int,
        state_data: Optional[Dict[str, Any]] = None
    ) -> AgentState:
        """Update agent execution state"""
        
        state = await self.state_repo.update_state(
            session_id=session_id,
            current_state=current_state,
            iteration_count=iteration,
            state_data=state_data
        )
        
        if not state:
            raise ValueError(f"Agent state not found for session {session_id}")
        
        return state
    
    async def record_token_usage(
        self,
        session_id: str,
        input_tokens: int,
        output_tokens: int
    ) -> AgentState:
        """Record token usage"""
        
        state = await self.state_repo.update_token_usage(
            session_id=session_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )
        
        if not state:
            raise ValueError(f"Agent state not found for session {session_id}")
        
        return state
    
    async def record_tool_call(
        self,
        session_id: str,
        success: bool
    ) -> AgentState:
        """Record tool call statistics"""
        
        state = await self.state_repo.update_tool_stats(
            session_id=session_id,
            success=success
        )
        
        if not state:
            raise ValueError(f"Agent state not found for session {session_id}")
        
        return state
    
    async def record_error(
        self,
        session_id: str,
        error_message: str
    ) -> AgentState:
        """Record an error"""
        
        state = await self.state_repo.record_error(
            session_id=session_id,
            error_message=error_message
        )
        
        if not state:
            raise ValueError(f"Agent state not found for session {session_id}")
        
        return state
    
    async def create_checkpoint(
        self,
        session_id: str,
        iteration: int,
        checkpoint_type: str = "auto",
        reason: Optional[str] = None
    ) -> AgentState:
        """Create a checkpoint"""
        
        # Get agent state
        state = await self.state_repo.get_by_session(session_id)
        if not state:
            raise ValueError(f"Agent state not found for session {session_id}")
        
        # Capture context snapshot
        context_snapshot = {
            "current_state": state.current_state,
            "iteration": state.iteration_count,
            "token_usage": {
                "input": state.input_tokens_used,
                "output": state.output_tokens_used,
                "total": state.total_tokens_used
            },
            "tool_stats": {
                "total": state.tool_calls_count,
                "success": state.tool_calls_success,
                "failed": state.tool_calls_failed
            },
            "errors": {
                "count": state.error_count,
                "last_error": state.last_error,
                "last_error_time": state.last_error_time.isoformat() if state.last_error_time else None
            }
        }
        
        # Capture working memory snapshot
        filesystem = AgentFileSystem()
        memory_manager = ThreeFilesManager(filesystem, session_id)
        
        try:
            memory_data = memory_manager.read_all()
            working_memory_snapshot = {
                "task_plan": memory_data["task_plan"]["content"][:500],
                "findings": memory_data["findings"]["content"][:300],
                "progress": memory_data["progress"]["content"][:300]
            }
        except Exception:
            working_memory_snapshot = None
        
        # Create checkpoint
        checkpoint = await self.checkpoint_repo.create(
            agent_state_id=state.id,
            iteration=iteration,
            checkpoint_type=checkpoint_type,
            context_snapshot=context_snapshot,
            working_memory_snapshot=working_memory_snapshot,
            reason=reason
        )
        
        return state
    
    async def complete_session(
        self,
        session_id: str,
        total_execution_time: Optional[float] = None
    ) -> AgentState:
        """Mark session as completed"""
        
        state = await self.state_repo.complete_session(
            session_id=session_id,
            total_execution_time=total_execution_time
        )
        
        if not state:
            raise ValueError(f"Agent state not found for session {session_id}")
        
        return state
    
    async def get_state_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get agent state summary"""
        
        state = await self.state_repo.get_by_session(session_id)
        if not state:
            return None
        
        # Get recent checkpoints
        checkpoints = await self.checkpoint_repo.get_by_agent_state(
            agent_state_id=state.id,
            limit=5
        )
        
        return {
            "session_id": session_id,
            "current_state": state.current_state,
            "iteration": state.iteration_count,
            "token_usage": {
                "input": state.input_tokens_used,
                "output": state.output_tokens_used,
                "total": state.total_tokens_used
            },
            "tool_stats": {
                "total": state.tool_calls_count,
                "success": state.tool_calls_success,
                "failed": state.tool_calls_failed,
                "success_rate": (
                    state.tool_calls_success / state.tool_calls_count * 100
                    if state.tool_calls_count > 0 else 0
                )
            },
            "errors": {
                "count": state.error_count,
                "last_error": state.last_error,
                "last_error_time": state.last_error_time.isoformat() if state.last_error_time else None
            },
            "performance": {
                "average_iteration_time": state.average_iteration_time,
                "total_execution_time": state.total_execution_time
            },
            "timestamps": {
                "started_at": state.started_at.isoformat() if state.started_at else None,
                "last_activity_at": state.last_activity_at.isoformat() if state.last_activity_at else None,
                "completed_at": state.completed_at.isoformat() if state.completed_at else None
            },
            "recent_checkpoints": [
                {
                    "id": cp.id,
                    "iteration": cp.iteration,
                    "type": cp.checkpoint_type,
                    "reason": cp.reason,
                    "created_at": cp.created_at.isoformat()
                }
                for cp in checkpoints
            ]
        }
    
    async def cleanup_old_checkpoints(
        self,
        session_id: str,
        keep_last_n: int = 5
    ) -> int:
        """Clean up old checkpoints"""
        
        state = await self.state_repo.get_by_session(session_id)
        if not state:
            return 0
        
        return await self.checkpoint_repo.delete_old_checkpoints(
            agent_state_id=state.id,
            keep_last_n=keep_last_n
        )
