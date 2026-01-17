
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.agent_config import AgentConfig, LLMModel, LLMProvider


class AgentConfigRepository:
    """Repository for AgentConfig operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        workspace_id: str,
        name: str,
        description: str | None = None,
        llm_provider: str = "anthropic",
        llm_model: str = "claude-3-5-sonnet-20241022",
        llm_max_tokens: int = 8192,
        llm_temperature: float = 1.0,
        llm_top_p: float | None = None,
        llm_top_k: int | None = None,
        max_iterations: int = 20,
        enable_skills: bool = True,
        enable_hybrid_execution: bool = True,
        enabled_tools: list[str] | None = None,
        tool_risk_threshold: str = "MEDIUM",
        enable_working_memory: bool = True,
        enable_long_memory: bool = False,
        memory_retention_days: int | None = 30,
        custom_system_prompt: str | None = None,
        additional_context: str | None = None,
        metadata: dict | None = None,
        created_by: str | None = None
    ) -> AgentConfig:
        """Create a new agent configuration"""
        import uuid

        config = AgentConfig(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            name=name,
            description=description,
            llm_provider=llm_provider,
            llm_model=llm_model,
            llm_max_tokens=llm_max_tokens,
            llm_temperature=llm_temperature,
            llm_top_p=llm_top_p,
            llm_top_k=llm_top_k,
            max_iterations=max_iterations,
            enable_skills=enable_skills,
            enable_hybrid_execution=enable_hybrid_execution,
            enabled_tools=enabled_tools,
            tool_risk_threshold=tool_risk_threshold,
            enable_working_memory=enable_working_memory,
            enable_long_memory=enable_long_memory,
            memory_retention_days=memory_retention_days,
            custom_system_prompt=custom_system_prompt,
            additional_context=additional_context,
            metadata=metadata or {},
            created_by=created_by
        )

        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)

        return config

    async def get_by_id(self, config_id: str) -> AgentConfig | None:
        """Get agent configuration by ID"""
        result = await self.db.execute(
            select(AgentConfig)
            .options(selectinload(AgentConfig.workspace))
            .where(AgentConfig.id == config_id)
        )
        return result.scalar_one_or_none()

    async def get_by_workspace(
        self,
        workspace_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[list[AgentConfig], int]:
        """Get agent configurations by workspace"""
        # Get total count
        count_result = await self.db.execute(
            select(AgentConfig.id)
            .where(AgentConfig.workspace_id == workspace_id)
        )
        total = len(count_result.all())

        # Get items
        result = await self.db.execute(
            select(AgentConfig)
            .where(AgentConfig.workspace_id == workspace_id)
            .order_by(AgentConfig.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        items = result.scalars().all()

        return list(items), total

    async def update(
        self,
        config_id: str,
        **kwargs
    ) -> AgentConfig | None:
        """Update agent configuration"""
        config = await self.get_by_id(config_id)
        if not config:
            return None

        for key, value in kwargs.items():
            if hasattr(config, key) and value is not None:
                setattr(config, key, value)

        await self.db.commit()
        await self.db.refresh(config)

        return config

    async def delete(self, config_id: str) -> bool:
        """Delete agent configuration"""
        config = await self.get_by_id(config_id)
        if not config:
            return False

        await self.db.delete(config)
        await self.db.commit()

        return True

    async def get_default_for_workspace(self, workspace_id: str) -> AgentConfig | None:
        """Get default agent configuration for workspace"""
        result = await self.db.execute(
            select(AgentConfig)
            .where(AgentConfig.workspace_id == workspace_id)
            .order_by(AgentConfig.created_at.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class LLMProviderRepository:
    """Repository for LLMProvider operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, active_only: bool = True) -> list[LLMProvider]:
        """Get all LLM providers"""
        query = select(LLMProvider)
        if active_only:
            query = query.where(LLMProvider.is_active)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, provider_id: str) -> LLMProvider | None:
        """Get LLM provider by ID"""
        result = await self.db.execute(
            select(LLMProvider)
            .options(selectinload(LLMProvider.models))
            .where(LLMProvider.id == provider_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> LLMProvider | None:
        """Get LLM provider by name"""
        result = await self.db.execute(
            select(LLMProvider)
            .options(selectinload(LLMProvider.models))
            .where(LLMProvider.name == name)
        )
        return result.scalar_one_or_none()


class LLMModelRepository:
    """Repository for LLMModel operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, active_only: bool = True) -> list[LLMModel]:
        """Get all LLM models"""
        query = select(LLMModel)
        if active_only:
            query = query.where(LLMModel.is_active)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_provider(self, provider_id: str, active_only: bool = True) -> list[LLMModel]:
        """Get LLM models by provider"""
        query = select(LLMModel).where(LLMModel.provider_id == provider_id)
        if active_only:
            query = query.where(LLMModel.is_active)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, model_id: str) -> LLMModel | None:
        """Get LLM model by ID"""
        result = await self.db.execute(
            select(LLMModel)
            .options(selectinload(LLMModel.provider))
            .where(LLMModel.id == model_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> LLMModel | None:
        """Get LLM model by name"""
        result = await self.db.execute(
            select(LLMModel)
            .options(selectinload(LLMModel.provider))
            .where(LLMModel.name == name)
        )
        return result.scalar_one_or_none()
