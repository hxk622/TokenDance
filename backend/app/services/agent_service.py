from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.engine import AgentEngine
from app.agent.tools.init_tools import register_builtin_tools
from app.agent.tools.registry import get_global_registry
from app.core.config import Settings
from app.filesystem import AgentFileSystem
from app.models.agent_config import AgentConfig
from app.models.session import Session
from app.services.agent_config_service import AgentConfigService


class AgentService:
    """Service for managing Agent lifecycle and execution"""

    def __init__(
        self,
        db: AsyncSession,
        settings: Settings,
        config_service: AgentConfigService
    ):
        self.db = db
        self.settings = settings
        self.config_service = config_service
        self._active_agents: dict[str, AgentEngine] = {}

    async def create_agent_for_session(
        self,
        session: Session,
        config: AgentConfig | None = None
    ) -> AgentEngine:
        """Create AgentEngine for a session"""

        # Get or use default configuration
        if not config:
            config = await self.config_service.create_default_config(
                workspace_id=session.workspace_id,
                user_id="system"
            )

        # Get LLM client
        llm = await self.config_service.get_llm_client(config)

        # Create filesystem for workspace
        filesystem = AgentFileSystem()

        # Create AgentEngine
        agent = AgentEngine(
            llm=llm,
            filesystem=filesystem,
            workspace_id=session.workspace_id,
            session_id=session.id,
            max_iterations=config.max_iterations,
            enable_skills=config.enable_skills
        )

        # Configure tools based on config
        if config.enabled_tools:
            agent.tool_registry.set_allowed_tools(config.enabled_tools)

        # Cache agent
        self._active_agents[session.id] = agent

        return agent

    async def get_agent_for_session(self, session_id: str) -> AgentEngine | None:
        """Get existing AgentEngine for a session"""
        return self._active_agents.get(session_id)

    async def execute_task(
        self,
        session_id: str,
        user_message: str,
        config: AgentConfig | None = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Execute a task using Agent"""

        # Get session
        from sqlalchemy import select

        from app.models.session import Session

        result = await self.db.execute(
            select(Session).where(Session.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Get or create agent
        agent = await self.get_agent_for_session(session_id)
        if not agent:
            agent = await self.create_agent_for_session(session, config)

        # Execute task
        response = await agent.run(user_message)

        # Yield response as stream events
        yield {
            "type": "answer",
            "content": response.answer,
            "reasoning": response.reasoning,
            "tool_calls": response.tool_calls,
            "token_usage": response.token_usage,
            "iterations": response.iterations
        }

    async def stream_task(
        self,
        session_id: str,
        user_message: str,
        config: AgentConfig | None = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream task execution with SSE events"""

        # Get session
        from sqlalchemy import select

        from app.models.session import Session

        result = await self.db.execute(
            select(Session).where(Session.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Get or create agent
        agent = await self.get_agent_for_session(session_id)
        if not agent:
            agent = await self.create_agent_for_session(session, config)

        # Stream execution (TODO: implement streaming)
        # For now, fall back to execute_task
        async for event in self.execute_task(session_id, user_message, config):
            yield event

    async def stop_agent(self, session_id: str) -> bool:
        """Stop agent execution for a session"""
        agent = self._active_agents.get(session_id)
        if agent:
            # TODO: Implement agent.stop()
            # await agent.stop()
            del self._active_agents[session_id]
            return True
        return False

    async def cleanup_agent(self, session_id: str) -> None:
        """Clean up agent resources"""
        agent = self._active_agents.get(session_id)
        if agent:
            del self._active_agents[session_id]

    async def get_agent_status(self, session_id: str) -> dict[str, Any] | None:
        """Get agent execution status"""
        agent = self._active_agents.get(session_id)
        if not agent:
            return None

        return {
            "session_id": session_id,
            "is_active": True,
            "iteration": agent.iteration_count,
            "state": agent.state_machine.current_state.value if hasattr(agent, 'state_machine') else "unknown",
            "tokens_used": agent.context_manager.get_token_usage() if hasattr(agent, 'context_manager') else {}
        }

    async def initialize_tools(self) -> int:
        """Initialize and register all built-in tools"""
        registry = get_global_registry()

        if len(registry) == 0:
            tools = register_builtin_tools(registry)
            return len(tools)

        return len(registry)

    async def get_available_tools(self) -> dict[str, Any]:
        """Get available tools information"""
        registry = get_global_registry()

        # Initialize if needed
        if len(registry) == 0:
            await self.initialize_tools()

        return {
            "total": len(registry),
            "tools": registry.list_schemas(),
            "categories": {
                "Web & Research": ["web_search", "read_url"],
                "File Operations": ["file_ops", "create_document"],
                "System": ["shell", "exit"],
                "Content Generation": ["image_generation", "ppt_generator", "report_generator"]
            }
        }
