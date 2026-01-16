from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


class AgentConfigBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Agent configuration name")
    description: Optional[str] = Field(None, max_length=1000, description="Agent configuration description")
    
    # LLM Configuration
    llm_provider: str = Field("anthropic", description="LLM provider (anthropic, openai, etc.)")
    llm_model: str = Field("claude-3-5-sonnet-20241022", description="LLM model name")
    llm_max_tokens: int = Field(8192, ge=1, le=128000, description="Maximum output tokens")
    llm_temperature: float = Field(1.0, ge=0.0, le=2.0, description="Temperature parameter")
    llm_top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Top-p sampling parameter")
    llm_top_k: Optional[int] = Field(None, ge=1, description="Top-k sampling parameter")
    
    # Agent Behavior
    max_iterations: int = Field(20, ge=1, le=100, description="Maximum iterations per task")
    enable_skills: bool = Field(True, description="Enable skill system")
    enable_hybrid_execution: bool = Field(True, description="Enable hybrid execution")
    
    # Tool Configuration
    enabled_tools: Optional[List[str]] = Field(None, description="List of enabled tool names")
    tool_risk_threshold: Literal["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        "MEDIUM", description="Maximum risk level for auto-approval"
    )
    
    # Memory Configuration
    enable_working_memory: bool = Field(True, description="Enable working memory")
    enable_long_memory: bool = Field(False, description="Enable long-term memory")
    memory_retention_days: Optional[int] = Field(30, ge=1, description="Memory retention period in days")
    
    # Advanced Settings
    custom_system_prompt: Optional[str] = Field(None, max_length=10000, description="Custom system prompt")
    additional_context: Optional[str] = Field(None, max_length=5000, description="Additional context")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class AgentConfigCreate(AgentConfigBase):
    workspace_id: str = Field(..., description="Workspace ID")


class AgentConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    
    # LLM Configuration
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_max_tokens: Optional[int] = Field(None, ge=1, le=128000)
    llm_temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    llm_top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    llm_top_k: Optional[int] = Field(None, ge=1)
    
    # Agent Behavior
    max_iterations: Optional[int] = Field(None, ge=1, le=100)
    enable_skills: Optional[bool] = None
    enable_hybrid_execution: Optional[bool] = None
    
    # Tool Configuration
    enabled_tools: Optional[List[str]] = None
    tool_risk_threshold: Optional[Literal["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]] = None
    
    # Memory Configuration
    enable_working_memory: Optional[bool] = None
    enable_long_memory: Optional[bool] = None
    memory_retention_days: Optional[int] = Field(None, ge=1)
    
    # Advanced Settings
    custom_system_prompt: Optional[str] = Field(None, max_length=10000)
    additional_context: Optional[str] = Field(None, max_length=5000)
    metadata: Optional[Dict[str, Any]] = None


class AgentConfigResponse(AgentConfigBase):
    id: str
    workspace_id: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    class Config:
        from_attributes = True


class LLMProviderResponse(BaseModel):
    id: str
    name: str
    display_name: str
    description: Optional[str]
    api_base_url: Optional[str]
    requires_api_key: bool
    supported_models: List[str]
    supports_streaming: bool
    supports_tools: bool
    supports_vision: bool
    max_context_tokens: Optional[int]
    input_price_per_1m: Optional[float]
    output_price_per_1m: Optional[float]
    is_active: bool
    is_builtin: bool
    
    class Config:
        from_attributes = True


class LLMModelResponse(BaseModel):
    id: str
    provider_id: str
    name: str
    display_name: str
    description: Optional[str]
    max_tokens: int
    max_context_tokens: int
    supports_streaming: bool
    supports_tools: bool
    supports_vision: bool
    input_price_per_1m: Optional[float]
    output_price_per_1m: Optional[float]
    recommended_temperature: float
    recommended_max_tokens: Optional[int]
    is_active: bool
    
    class Config:
        from_attributes = True


class AgentConfigListResponse(BaseModel):
    items: List[AgentConfigResponse]
    total: int
    limit: int
    offset: int
