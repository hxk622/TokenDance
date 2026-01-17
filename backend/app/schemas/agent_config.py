from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AgentConfigBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Agent configuration name")
    description: str | None = Field(None, max_length=1000, description="Agent configuration description")

    # LLM Configuration
    llm_provider: str = Field("anthropic", description="LLM provider (anthropic, openai, etc.)")
    llm_model: str = Field("claude-3-5-sonnet-20241022", description="LLM model name")
    llm_max_tokens: int = Field(8192, ge=1, le=128000, description="Maximum output tokens")
    llm_temperature: float = Field(1.0, ge=0.0, le=2.0, description="Temperature parameter")
    llm_top_p: float | None = Field(None, ge=0.0, le=1.0, description="Top-p sampling parameter")
    llm_top_k: int | None = Field(None, ge=1, description="Top-k sampling parameter")

    # Agent Behavior
    max_iterations: int = Field(20, ge=1, le=100, description="Maximum iterations per task")
    enable_skills: bool = Field(True, description="Enable skill system")
    enable_hybrid_execution: bool = Field(True, description="Enable hybrid execution")

    # Tool Configuration
    enabled_tools: list[str] | None = Field(None, description="List of enabled tool names")
    tool_risk_threshold: Literal["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        "MEDIUM", description="Maximum risk level for auto-approval"
    )

    # Memory Configuration
    enable_working_memory: bool = Field(True, description="Enable working memory")
    enable_long_memory: bool = Field(False, description="Enable long-term memory")
    memory_retention_days: int | None = Field(30, ge=1, description="Memory retention period in days")

    # Advanced Settings
    custom_system_prompt: str | None = Field(None, max_length=10000, description="Custom system prompt")
    additional_context: str | None = Field(None, max_length=5000, description="Additional context")
    metadata: dict[str, Any] | None = Field(default_factory=dict, description="Additional metadata")


class AgentConfigCreate(AgentConfigBase):
    workspace_id: str = Field(..., description="Workspace ID")


class AgentConfigUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)

    # LLM Configuration
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_max_tokens: int | None = Field(None, ge=1, le=128000)
    llm_temperature: float | None = Field(None, ge=0.0, le=2.0)
    llm_top_p: float | None = Field(None, ge=0.0, le=1.0)
    llm_top_k: int | None = Field(None, ge=1)

    # Agent Behavior
    max_iterations: int | None = Field(None, ge=1, le=100)
    enable_skills: bool | None = None
    enable_hybrid_execution: bool | None = None

    # Tool Configuration
    enabled_tools: list[str] | None = None
    tool_risk_threshold: Literal["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"] | None = None

    # Memory Configuration
    enable_working_memory: bool | None = None
    enable_long_memory: bool | None = None
    memory_retention_days: int | None = Field(None, ge=1)

    # Advanced Settings
    custom_system_prompt: str | None = Field(None, max_length=10000)
    additional_context: str | None = Field(None, max_length=5000)
    metadata: dict[str, Any] | None = None


class AgentConfigResponse(AgentConfigBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None
    updated_by: str | None = None


class LLMProviderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    display_name: str
    description: str | None
    api_base_url: str | None
    requires_api_key: bool
    supported_models: list[str]
    supports_streaming: bool
    supports_tools: bool
    supports_vision: bool
    max_context_tokens: int | None
    input_price_per_1m: float | None
    output_price_per_1m: float | None
    is_active: bool
    is_builtin: bool


class LLMModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider_id: str
    name: str
    display_name: str
    description: str | None
    max_tokens: int
    max_context_tokens: int
    supports_streaming: bool
    supports_tools: bool
    supports_vision: bool
    input_price_per_1m: float | None
    output_price_per_1m: float | None
    recommended_temperature: float
    recommended_max_tokens: int | None
    is_active: bool


class AgentConfigListResponse(BaseModel):
    items: list[AgentConfigResponse]
    total: int
    limit: int
    offset: int
