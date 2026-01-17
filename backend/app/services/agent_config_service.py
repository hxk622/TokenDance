from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.llm.anthropic import ClaudeLLM
from app.agent.llm.base import BaseLLM
from app.core.config import Settings
from app.models.agent_config import AgentConfig, LLMModel
from app.repositories.agent_config_repository import (
    AgentConfigRepository,
    LLMModelRepository,
    LLMProviderRepository,
)


class AgentConfigService:
    """Service for managing Agent configurations"""

    def __init__(self, db: AsyncSession, settings: Settings):
        self.db = db
        self.settings = settings
        self.config_repo = AgentConfigRepository(db)
        self.provider_repo = LLMProviderRepository(db)
        self.model_repo = LLMModelRepository(db)

    async def create_default_config(
        self,
        workspace_id: str,
        user_id: str,
        name: str = "Default Agent"
    ) -> AgentConfig:
        """Create default agent configuration for a workspace"""
        config = await self.config_repo.create(
            workspace_id=workspace_id,
            name=name,
            description="Default agent configuration",
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022",
            llm_max_tokens=8192,
            llm_temperature=1.0,
            max_iterations=20,
            enable_skills=True,
            enable_hybrid_execution=True,
            enable_working_memory=True,
            enable_long_memory=False,
            tool_risk_threshold="MEDIUM",
            created_by=user_id
        )
        return config

    async def get_llm_client(self, config: AgentConfig) -> BaseLLM:
        """Get LLM client instance from configuration"""

        # Get provider info
        provider = await self.provider_repo.get_by_name(config.llm_provider)
        if not provider:
            raise ValueError(f"LLM provider '{config.llm_provider}' not found")

        # Get API key based on provider
        api_key = self._get_api_key(provider.name)

        # Create client based on provider
        if provider.name == "anthropic":
            return ClaudeLLM(
                api_key=api_key,
                model=config.llm_model,
                max_tokens=config.llm_max_tokens,
                temperature=config.llm_temperature,
                base_url=provider.api_base_url
            )
        elif provider.name == "openai":
            # TODO: Implement OpenAI client
            raise NotImplementedError("OpenAI client not yet implemented")
        else:
            raise ValueError(f"Unsupported LLM provider: {provider.name}")

    def _get_api_key(self, provider_name: str) -> str:
        """Get API key for provider"""
        if provider_name == "anthropic":
            api_key = self.settings.ANTHROPIC_API_KEY
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            return api_key
        elif provider_name == "openai":
            api_key = getattr(self.settings, "OPENAI_API_KEY", None)
            if not api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            return api_key
        else:
            raise ValueError(f"Unknown provider: {provider_name}")

    async def get_config_for_session(self, session_id: str) -> AgentConfig | None:
        """Get agent configuration for a session"""
        from sqlalchemy import select

        from app.models.session import Session

        result = await self.db.execute(
            select(Session).where(Session.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session or not session.agent_config_id:
            return None

        return await self.config_repo.get_by_id(session.agent_config_id)

    async def get_available_models(self, provider_name: str | None = None) -> list[LLMModel]:
        """Get available LLM models"""
        if provider_name:
            provider = await self.provider_repo.get_by_name(provider_name)
            if not provider:
                return []
            return await self.model_repo.get_by_provider(provider.id)
        else:
            return await self.model_repo.get_all()

    async def get_model_info(self, model_name: str) -> LLMModel | None:
        """Get model information"""
        return await self.model_repo.get_by_name(model_name)

    async def validate_config(self, config_data: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate agent configuration"""

        # Check provider exists
        provider = await self.provider_repo.get_by_name(config_data.get("llm_provider", "anthropic"))
        if not provider:
            return False, f"LLM provider '{config_data.get('llm_provider')}' not found"

        # Check model exists
        model = await self.model_repo.get_by_name(config_data.get("llm_model"))
        if not model:
            return False, f"LLM model '{config_data.get('llm_model')}' not found"

        # Check model belongs to provider
        if model.provider_id != provider.id:
            return False, f"Model '{model.name}' does not belong to provider '{provider.name}'"

        # Validate tool risk threshold
        valid_thresholds = ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
        threshold = config_data.get("tool_risk_threshold", "MEDIUM")
        if threshold not in valid_thresholds:
            return False, f"Invalid tool_risk_threshold: {threshold}"

        return True, None

    async def get_config_summary(self, config: AgentConfig) -> dict[str, Any]:
        """Get configuration summary for display"""
        provider = await self.provider_repo.get_by_name(config.llm_provider)
        model = await self.model_repo.get_by_name(config.llm_model)

        return {
            "id": config.id,
            "name": config.name,
            "llm_provider": provider.display_name if provider else config.llm_provider,
            "llm_model": model.display_name if model else config.llm_model,
            "max_iterations": config.max_iterations,
            "enable_skills": config.enable_skills,
            "enable_working_memory": config.enable_working_memory,
            "tool_risk_threshold": config.tool_risk_threshold,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat()
        }
