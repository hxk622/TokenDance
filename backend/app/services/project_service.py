"""
Project service - business logic layer for projects.
"""
import logging
from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import utc_now_naive
from app.models.conversation import Conversation, ConversationPurpose, ConversationStatus
from app.models.project import Project, ProjectStatus, ProjectType
from app.models.project_version import ProjectVersion, VersionChangeType
from app.models.session import Session, SessionStatus
from app.repositories.project_repository import ProjectRepository
from app.schemas.conversation import ConversationCreate, SelectionContext
from app.schemas.project import ProjectCreate, ProjectUpdate

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for Project business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ProjectRepository(db)

    # ============ Project CRUD ============

    async def create_project(self, data: ProjectCreate) -> Project:
        """Create a new project."""
        project = await self.repo.create(
            workspace_id=data.workspace_id,
            intent=data.intent,
            title=data.title,
            description=data.description,
            project_type=data.project_type,
            settings=data.settings.model_dump() if data.settings else None,
        )
        logger.info(f"Created project {project.id} with type {project.project_type.value}")
        return project

    async def get_project(
        self,
        project_id: str,
        include_conversations: bool = False,
        include_artifacts: bool = False,
    ) -> Project | None:
        """Get project by ID."""
        project = await self.repo.get_by_id(
            project_id,
            include_conversations=include_conversations,
            include_artifacts=include_artifacts,
        )
        if project:
            # Touch to update last_accessed_at
            await self.repo.touch(project_id)
        return project

    async def list_projects(
        self,
        workspace_id: str,
        limit: int = 20,
        offset: int = 0,
        status: ProjectStatus | None = None,
        project_type: ProjectType | None = None,
    ) -> tuple[list[Project], int]:
        """List projects with pagination."""
        return await self.repo.get_by_workspace(
            workspace_id=workspace_id,
            limit=limit,
            offset=offset,
            status=status,
            project_type=project_type,
        )

    async def update_project(
        self,
        project_id: str,
        data: ProjectUpdate,
    ) -> Project | None:
        """Update project."""
        updates = data.model_dump(exclude_unset=True)
        if "context" in updates and updates["context"]:
            updates["context"] = updates["context"]
        if "settings" in updates and updates["settings"]:
            updates["settings"] = updates["settings"]
        return await self.repo.update(project_id, **updates)

    async def archive_project(self, project_id: str) -> Project | None:
        """Archive project (soft delete)."""
        project = await self.repo.archive_project(project_id)
        if project:
            logger.info(f"Archived project {project_id}")
        return project

    async def delete_project(self, project_id: str) -> bool:
        """Hard delete project."""
        result = await self.repo.delete(project_id)
        if result:
            logger.info(f"Deleted project {project_id}")
        return result

    # ============ Conversation Management ============

    async def create_conversation(
        self,
        project_id: str,
        data: ConversationCreate | None = None,
    ) -> Conversation | None:
        """Create a new conversation within a project."""
        project = await self.repo.get_by_id(project_id)
        if not project:
            return None

        # Create conversation
        conversation = Conversation(
            id=str(uuid4()),
            project_id=project_id,
            title=data.title if data and data.title else "New Conversation",
            purpose=data.purpose if data else ConversationPurpose.GENERAL,
            status=ConversationStatus.ACTIVE,
        )

        # Set selection context if provided
        if data and data.selection:
            conversation.selection_context = {
                "artifact_id": data.selection.artifact_id,
                "selected_text": data.selection.selected_text,
                "selection_range": {
                    "start": data.selection.selection_range.start,
                    "end": data.selection.selection_range.end,
                }
            }

        self.db.add(conversation)

        # Update project stats and status
        project.conversation_count += 1
        if project.status == ProjectStatus.DRAFT:
            project.status = ProjectStatus.IN_PROGRESS

        await self.db.commit()
        await self.db.refresh(conversation)

        logger.info(f"Created conversation {conversation.id} in project {project_id}")
        return conversation

    async def get_or_create_conversation(
        self,
        project_id: str,
        conversation_id: str | None = None,
        selection: SelectionContext | None = None,
    ) -> Conversation | None:
        """Get existing conversation or create a new one."""
        if conversation_id:
            # Get specific conversation
            from sqlalchemy import select
            query = select(Conversation).where(Conversation.id == conversation_id)
            result = await self.db.execute(query)
            conversation = result.scalar_one_or_none()
            if conversation:
                # Update selection if provided
                if selection:
                    conversation.selection_context = {
                        "artifact_id": selection.artifact_id,
                        "selected_text": selection.selected_text,
                        "selection_range": {
                            "start": selection.selection_range.start,
                            "end": selection.selection_range.end,
                        }
                    }
                    await self.db.commit()
                return conversation

        # Get latest active conversation or create new one
        latest = await self.repo.get_latest_conversation(project_id)
        if latest and latest.status == ConversationStatus.ACTIVE:
            if selection:
                latest.selection_context = {
                    "artifact_id": selection.artifact_id,
                    "selected_text": selection.selected_text,
                    "selection_range": {
                        "start": selection.selection_range.start,
                        "end": selection.selection_range.end,
                    }
                }
                await self.db.commit()
            return latest

        # Create new conversation
        return await self.create_conversation(
            project_id,
            ConversationCreate(
                purpose=ConversationPurpose.REFINEMENT if selection else ConversationPurpose.GENERAL,
                selection=selection,
            )
        )

    async def complete_conversation(self, conversation_id: str) -> Conversation | None:
        """Mark conversation as completed."""
        from sqlalchemy import select
        query = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.db.execute(query)
        conversation = result.scalar_one_or_none()
        if not conversation:
            return None

        conversation.status = ConversationStatus.COMPLETED
        conversation.completed_at = utc_now_naive()
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation

    # ============ Context Management ============

    async def add_decision(
        self,
        project_id: str,
        decision: str,
        reason: str | None = None,
    ) -> Project | None:
        """Add a decision to project context."""
        return await self.repo.add_decision(project_id, decision, reason)

    async def add_failure(
        self,
        project_id: str,
        failure_type: str,
        message: str,
        learning: str | None = None,
    ) -> Project | None:
        """Add a failure record to project context (Keep the Failures)."""
        return await self.repo.add_failure(project_id, failure_type, message, learning)

    async def add_finding(
        self,
        project_id: str,
        finding: str,
        source: str | None = None,
    ) -> Project | None:
        """Add a key finding to project context."""
        return await self.repo.add_finding(project_id, finding, source)

    async def get_context_for_llm(self, project_id: str) -> dict[str, Any]:
        """Build context dictionary for LLM prompt."""
        project = await self.repo.get_by_id(project_id, include_artifacts=True)
        if not project:
            return {}

        context = {
            "intent": project.intent,
            "decisions": project.context.get("decisions", [])[-5:],  # Last 5
            "failures": project.context.get("failures", [])[-5:],    # Last 5 (Keep the Failures)
            "key_findings": project.context.get("key_findings", [])[-10:],  # Last 10
        }

        # Add artifact summaries
        if project.artifacts:
            latest_artifacts = [a for a in project.artifacts if a.is_latest]
            context["artifacts"] = [
                {
                    "id": a.id,
                    "name": a.name,
                    "type": a.artifact_type.value,
                    "preview": a.content_preview,
                }
                for a in latest_artifacts[:5]  # Max 5 artifacts
            ]

        return context

    # ============ Version Management ============

    async def create_version(
        self,
        project_id: str,
        change_summary: str,
        change_type: VersionChangeType = VersionChangeType.AUTO,
        changed_by: str = "ai",
    ) -> ProjectVersion | None:
        """Create a version snapshot of the project."""
        project = await self.repo.get_by_id(
            project_id,
            include_artifacts=True
        )
        if not project:
            return None

        # Get next version number
        version_number = await self.repo.get_latest_version_number(project_id) + 1

        # Build snapshot
        artifacts_snapshot = [
            {
                "id": a.id,
                "name": a.name,
                "version": a.version,
                "type": a.artifact_type.value,
            }
            for a in project.artifacts if a.is_latest
        ]

        version = ProjectVersion(
            id=str(uuid4()),
            project_id=project_id,
            version_number=version_number,
            snapshot={
                "artifacts": artifacts_snapshot,
                "context": project.context.copy(),
            },
            change_summary=change_summary,
            change_type=change_type,
            changed_by=changed_by,
        )

        self.db.add(version)
        await self.db.commit()
        await self.db.refresh(version)

        logger.info(f"Created version {version_number} for project {project_id}")
        return version

    # ============ Token Tracking ============

    async def add_tokens_used(
        self,
        project_id: str,
        tokens: int,
        conversation_id: str | None = None,
    ) -> None:
        """Track token usage for project and optionally conversation."""
        await self.repo.add_tokens_used(project_id, tokens)

        if conversation_id:
            from sqlalchemy import select
            query = select(Conversation).where(Conversation.id == conversation_id)
            result = await self.db.execute(query)
            conversation = result.scalar_one_or_none()
            if conversation:
                conversation.tokens_used += tokens
                await self.db.commit()

    # ============ Maintenance ============

    async def archive_inactive_quick_tasks(
        self,
        workspace_id: str,
        days: int = 7,
    ) -> int:
        """Archive quick task projects that have been inactive."""
        count = await self.repo.archive_inactive_quick_tasks(workspace_id, days)
        if count > 0:
            logger.info(f"Archived {count} inactive quick tasks in workspace {workspace_id}")
        return count

    # ============ Session Integration for SSE ============

    async def create_session_for_conversation(
        self,
        project_id: str,
        conversation_id: str,
        task: str,
    ) -> Session | None:
        """Create a Session for a Conversation to enable SSE streaming.

        This bridges Project Mode with the existing Session/SSE infrastructure.
        Each conversation execution maps to a Session for real-time streaming.

        Args:
            project_id: The project ID
            conversation_id: The conversation ID
            task: The user's message/task

        Returns:
            The created Session, or None if project not found
        """
        project = await self.repo.get_by_id(project_id)
        if not project:
            return None

        # Get conversation
        from sqlalchemy import select
        query = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.db.execute(query)
        conversation = result.scalar_one_or_none()
        if not conversation:
            return None

        # Create a new Session linked to this project's workspace
        session = Session(
            id=str(uuid4()),
            workspace_id=project.workspace_id,
            title=task[:100] if task else "Project Task",
            status=SessionStatus.PENDING,
            extra_data={
                "project_id": project_id,
                "conversation_id": conversation_id,
            }
        )
        self.db.add(session)

        # Link session to conversation
        conversation.current_session_id = session.id

        await self.db.commit()
        await self.db.refresh(session)

        logger.info(
            f"Created session {session.id} for conversation {conversation_id} "
            f"in project {project_id}"
        )
        return session

    async def get_conversation_session(
        self,
        conversation_id: str,
    ) -> Session | None:
        """Get the current session for a conversation."""
        from sqlalchemy import select
        query = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.db.execute(query)
        conversation = result.scalar_one_or_none()

        if not conversation or not conversation.current_session_id:
            return None

        session_query = select(Session).where(
            Session.id == conversation.current_session_id
        )
        session_result = await self.db.execute(session_query)
        return session_result.scalar_one_or_none()
