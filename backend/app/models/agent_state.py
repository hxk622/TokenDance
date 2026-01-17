from sqlalchemy import Column, String, Integer, Float, JSON, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class AgentState(Base):
    __tablename__ = "agent_states"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    
    # Agent Configuration
    agent_config_id = Column(String, ForeignKey("agent_configs.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Execution State
    current_state = Column(String(50), nullable=False, default="IDLE")
    iteration_count = Column(Integer, nullable=False, default=0)
    
    # Token Usage
    input_tokens_used = Column(Integer, nullable=False, default=0)
    output_tokens_used = Column(Integer, nullable=False, default=0)
    total_tokens_used = Column(Integer, nullable=False, default=0)
    
    # Tool Calls
    tool_calls_count = Column(Integer, nullable=False, default=0)
    tool_calls_success = Column(Integer, nullable=False, default=0)
    tool_calls_failed = Column(Integer, nullable=False, default=0)
    
    # Errors
    error_count = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    last_error_time = Column(DateTime, nullable=True)
    
    # Performance Metrics
    average_iteration_time = Column(Float, nullable=True)
    total_execution_time = Column(Float, nullable=True)
    
    # State Data (serialized)
    state_data = Column(JSON, nullable=True, default=dict)
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    session = relationship("Session", back_populates="agent_state")
    agent_config = relationship("AgentConfig")
    
    def __repr__(self):
        return f"<AgentState(session_id={self.session_id}, state={self.current_state})>"


class AgentCheckpoint(Base):
    __tablename__ = "agent_checkpoints"

    id = Column(String, primary_key=True)
    agent_state_id = Column(String, ForeignKey("agent_states.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Checkpoint Data
    iteration = Column(Integer, nullable=False)
    checkpoint_type = Column(String(50), nullable=False)  # "auto", "manual", "error"
    
    # Context Snapshot
    context_snapshot = Column(JSON, nullable=True)
    working_memory_snapshot = Column(JSON, nullable=True)
    
    # Metadata
    reason = Column(Text, nullable=True)
    checkpoint_metadata = Column(JSON, nullable=True, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    agent_state = relationship("AgentState", back_populates="checkpoints")
    
    def __repr__(self):
        return f"<AgentCheckpoint(id={self.id}, iteration={self.iteration}, type={self.checkpoint_type})>"
