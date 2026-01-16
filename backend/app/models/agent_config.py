from sqlalchemy import Column, String, Integer, Float, Boolean, JSON, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class AgentConfig(Base):
    __tablename__ = "agent_configs"

    id = Column(String, primary_key=True)
    workspace_id = Column(String, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # LLM Configuration
    llm_provider = Column(String(50), nullable=False, default="anthropic")
    llm_model = Column(String(100), nullable=False, default="claude-3-5-sonnet-20241022")
    llm_max_tokens = Column(Integer, nullable=False, default=8192)
    llm_temperature = Column(Float, nullable=False, default=1.0)
    llm_top_p = Column(Float, nullable=True)
    llm_top_k = Column(Integer, nullable=True)
    
    # Agent Behavior
    max_iterations = Column(Integer, nullable=False, default=20)
    enable_skills = Column(Boolean, nullable=False, default=True)
    enable_hybrid_execution = Column(Boolean, nullable=False, default=True)
    
    # Tool Configuration
    enabled_tools = Column(JSON, nullable=True, default=list)
    tool_risk_threshold = Column(String(20), nullable=False, default="MEDIUM")
    
    # Memory Configuration
    enable_working_memory = Column(Boolean, nullable=False, default=True)
    enable_long_memory = Column(Boolean, nullable=False, default=False)
    memory_retention_days = Column(Integer, nullable=True, default=30)
    
    # Advanced Settings
    custom_system_prompt = Column(Text, nullable=True)
    additional_context = Column(Text, nullable=True)
    agent_metadata = Column(JSON, nullable=True, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    updated_by = Column(String, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="agent_configs")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    sessions = relationship("Session", back_populates="agent_config", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AgentConfig(id={self.id}, name={self.name}, model={self.llm_model})>"


class LLMProvider(Base):
    __tablename__ = "llm_providers"

    id = Column(String, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Provider Configuration
    api_base_url = Column(String(255), nullable=True)
    requires_api_key = Column(Boolean, nullable=False, default=True)
    supported_models = Column(JSON, nullable=False, default=list)
    
    # Capabilities
    supports_streaming = Column(Boolean, nullable=False, default=True)
    supports_tools = Column(Boolean, nullable=False, default=True)
    supports_vision = Column(Boolean, nullable=False, default=False)
    max_context_tokens = Column(Integer, nullable=True)
    
    # Pricing (tokens per 1M)
    input_price_per_1m = Column(Float, nullable=True)
    output_price_per_1m = Column(Float, nullable=True)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    is_builtin = Column(Boolean, nullable=False, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<LLMProvider(name={self.name}, display_name={self.display_name})>"


class LLMModel(Base):
    __tablename__ = "llm_models"

    id = Column(String, primary_key=True)
    provider_id = Column(String, ForeignKey("llm_providers.id"), nullable=False, index=True)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Model Configuration
    max_tokens = Column(Integer, nullable=False)
    max_context_tokens = Column(Integer, nullable=False)
    
    # Capabilities
    supports_streaming = Column(Boolean, nullable=False, default=True)
    supports_tools = Column(Boolean, nullable=False, default=True)
    supports_vision = Column(Boolean, nullable=False, default=False)
    
    # Pricing
    input_price_per_1m = Column(Float, nullable=True)
    output_price_per_1m = Column(Float, nullable=True)
    
    # Recommended Settings
    recommended_temperature = Column(Float, nullable=False, default=1.0)
    recommended_max_tokens = Column(Integer, nullable=True)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    provider = relationship("LLMProvider", back_populates="models")
    
    def __repr__(self):
        return f"<LLMModel(name={self.name}, provider={self.provider_id})>"


# Update relationships
LLMProvider.models = relationship("LLMModel", back_populates="provider", cascade="all, delete-orphan")
