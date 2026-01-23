"""
Project repository - database access layer for projects.
"""
from typing import Any
from uuid import uuid4

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.datetime_utils import utc_now_naive
from app.models.artifact import Artifact
from app.models.conversation import Conversation
from app.models.project import Project, ProjectStatus, ProjectType
from app.models.project_version import ProjectVersion


class ProjectRepository:
    """Repository for Project database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        workspace_id: str,
        intent: str,
        title: str | None = None,
        description: str | None = None,
        project_type: ProjectType = ProjectType.QUICK_TASK,
        settings: dict[str, Any] | None = None,
    ) -> Project:
        """Create a new project."""
        # Auto-generate title from intent if not provided
        if not title:
            title = self._generate_title_from_intent(intent)

        project = Project(
            id=str(uuid4()),
            workspace_id=workspace_id,
            title=title,
            description=description,
            project_type=project_type,
            status=ProjectStatus.DRAFT,
            intent=intent,
            context={
                "decisions": [],
                "failures": [],
                "key_findings": [],
                "tags": [],
            },
            settings=settings or {
                "llm_model": "claude-3-5-sonnet-20241022",
                "skill_id": None,
            },
        )
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    def _generate_title_from_intent(self, intent: str, max_length: int = 50) -> str:
        """Generate a short title from the user's intent."""
        # Take first sentence or first N characters
        title = intent.split(".")[0].split("。")[0].split("\n")[0]
        if len(title) > max_length:
            title = title[:max_length - 3] + "..."
        return title or "New Project"

    async def get_by_id(
        self,
        project_id: str,
        include_conversations: bool = False,
        include_artifacts: bool = False,
        include_versions: bool = False,
    ) -> Project | None:
        """Get project by ID with optional eager loading."""
        query = select(Project).where(Project.id == project_id)

        # Eager load relationships if requested
        if include_conversations:
            query = query.options(selectinload(Project.conversations))
        if include_artifacts:
            query = query.options(selectinload(Project.artifacts))
        if include_versions:
            query = query.options(selectinload(Project.versions))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_workspace(
        self,
        workspace_id: str,
        limit: int = 20,
        offset: int = 0,
        status: ProjectStatus | None = None,
        project_type: ProjectType | None = None,
        exclude_archived: bool = True,
    ) -> tuple[list[Project], int]:
        """
        Get projects by workspace with pagination.
        Returns (projects, total_count).
        """
        # Build conditions
        conditions = [Project.workspace_id == workspace_id]
        if status:
            conditions.append(Project.status == status)
        elif exclude_archived:
            conditions.append(Project.status != ProjectStatus.ARCHIVED)
        if project_type:
            conditions.append(Project.project_type == project_type)

        # Count query
        count_query = select(func.count()).select_from(Project).where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()

        # Data query - order by last_accessed_at or updated_at
        query = (
            select(Project)
            .where(and_(*conditions))
            .order_by(
                Project.last_accessed_at.desc().nulls_last(),
                Project.updated_at.desc()
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        projects = list(result.scalars().all())

        return projects, total

    async def update(
        self,
        project_id: str,
        **updates: Any,
    ) -> Project | None:
        """Update project fields."""
        project = await self.get_by_id(project_id)
        if not project:
            return None

        for key, value in updates.items():
            if hasattr(project, key) and value is not None:
                setattr(project, key, value)

        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def update_status(
        self,
        project_id: str,
        status: ProjectStatus,
    ) -> Project | None:
        """Update project status."""
        return await self.update(project_id, status=status)

    async def start_project(self, project_id: str) -> Project | None:
        """Mark project as IN_PROGRESS."""
        return await self.update(
            project_id,
            status=ProjectStatus.IN_PROGRESS,
            last_accessed_at=utc_now_naive(),
        )

    async def complete_project(self, project_id: str) -> Project | None:
        """Mark project as COMPLETED."""
        return await self.update(project_id, status=ProjectStatus.COMPLETED)

    async def archive_project(self, project_id: str) -> Project | None:
        """Mark project as ARCHIVED (soft delete)."""
        return await self.update(project_id, status=ProjectStatus.ARCHIVED)

    async def touch(self, project_id: str) -> Project | None:
        """Update last_accessed_at timestamp."""
        return await self.update(project_id, last_accessed_at=utc_now_naive())

    async def add_decision(
        self,
        project_id: str,
        decision: str,
        reason: str | None = None,
    ) -> Project | None:
        """Add a decision to the project context."""
        project = await self.get_by_id(project_id)
        if not project:
            return None

        context = project.context.copy()
        if "decisions" not in context:
            context["decisions"] = []
        context["decisions"].append({
            "decision": decision,
            "reason": reason,
            "timestamp": utc_now_naive().isoformat(),
        })
        project.context = context

        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def add_failure(
        self,
        project_id: str,
        failure_type: str,
        message: str,
        learning: str | None = None,
    ) -> Project | None:
        """Add a failure record to the project context (Keep the Failures)."""
        project = await self.get_by_id(project_id)
        if not project:
            return None

        context = project.context.copy()
        if "failures" not in context:
            context["failures"] = []
        context["failures"].append({
            "type": failure_type,
            "message": message,
            "learning": learning,
            "timestamp": utc_now_naive().isoformat(),
        })
        project.context = context

        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def add_finding(
        self,
        project_id: str,
        finding: str,
        source: str | None = None,
    ) -> Project | None:
        """Add a key finding to the project context."""
        project = await self.get_by_id(project_id)
        if not project:
            return None

        context = project.context.copy()
        if "key_findings" not in context:
            context["key_findings"] = []
        context["key_findings"].append({
            "finding": finding,
            "source": source,
            "timestamp": utc_now_naive().isoformat(),
        })
        project.context = context

        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def add_tokens_used(
        self,
        project_id: str,
        tokens: int,
    ) -> Project | None:
        """Add tokens to project total."""
        project = await self.get_by_id(project_id)
        if not project:
            return None

        project.total_tokens_used += tokens
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def increment_conversation_count(self, project_id: str) -> Project | None:
        """Increment conversation count."""
        project = await self.get_by_id(project_id)
        if not project:
            return None

        project.conversation_count += 1
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def increment_artifact_count(self, project_id: str) -> Project | None:
        """Increment artifact count."""
        project = await self.get_by_id(project_id)
        if not project:
            return None

        project.artifact_count += 1
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def delete(self, project_id: str) -> bool:
        """Delete a project. Related items will be cascade deleted."""
        project = await self.get_by_id(project_id)
        if not project:
            return False

        await self.db.delete(project)
        await self.db.commit()
        return True

    async def get_conversation_count(self, project_id: str) -> int:
        """Get the number of conversations in a project."""
        query = (
            select(func.count())
            .select_from(Conversation)
            .where(Conversation.project_id == project_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_artifact_count(self, project_id: str) -> int:
        """Get the number of artifacts in a project."""
        query = (
            select(func.count())
            .select_from(Artifact)
            .where(
                and_(
                    Artifact.project_id == project_id,
                    Artifact.is_latest == True,  # noqa: E712
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_latest_conversation(
        self,
        project_id: str,
    ) -> Conversation | None:
        """Get the most recent conversation in a project."""
        query = (
            select(Conversation)
            .where(Conversation.project_id == project_id)
            .order_by(Conversation.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_latest_version_number(self, project_id: str) -> int:
        """Get the latest version number for a project."""
        query = (
            select(func.max(ProjectVersion.version_number))
            .where(ProjectVersion.project_id == project_id)
        )
        result = await self.db.execute(query)
        version = result.scalar_one_or_none()
        return version or 0

    async def archive_inactive_quick_tasks(
        self,
        workspace_id: str,
        days: int = 7,
    ) -> int:
        """Archive quick task projects that have been inactive for N days."""
        from datetime import timedelta

        cutoff_date = utc_now_naive() - timedelta(days=days)

        query = select(Project).where(
            and_(
                Project.workspace_id == workspace_id,
                Project.project_type == ProjectType.QUICK_TASK,
                Project.status != ProjectStatus.ARCHIVED,
                Project.updated_at < cutoff_date,
            )
        )
        result = await self.db.execute(query)
        projects = result.scalars().all()

        count = 0
        for project in projects:
            project.status = ProjectStatus.ARCHIVED
            count += 1

        await self.db.commit()
        return count
