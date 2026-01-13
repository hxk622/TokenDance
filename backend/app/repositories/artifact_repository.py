"""
Artifact repository - database access layer for artifacts.
"""
from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import Artifact, ArtifactType


class ArtifactRepository:
    """Repository for Artifact database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        session_id: str,
        name: str,
        artifact_type: ArtifactType,
        file_path: str,
        file_size: int = 0,
        description: Optional[str] = None,
        mime_type: Optional[str] = None,
        parent_step: Optional[str] = None,
        parent_message_id: Optional[str] = None,
        kv_anchor_id: Optional[str] = None,
        context_length: Optional[int] = None,
        extra_data: Optional[dict] = None,
    ) -> Artifact:
        """Create a new artifact."""
        artifact = Artifact(
            id=str(uuid4()),
            session_id=session_id,
            name=name,
            artifact_type=artifact_type,
            file_path=file_path,
            file_size=file_size,
            description=description,
            mime_type=mime_type,
            parent_step=parent_step,
            parent_message_id=parent_message_id,
            kv_anchor_id=kv_anchor_id,
            context_length=context_length,
            extra_data=extra_data or {},
        )
        self.db.add(artifact)
        await self.db.commit()
        await self.db.refresh(artifact)
        return artifact

    async def create_kv_snapshot(
        self,
        session_id: str,
        name: str,
        file_path: str,
        kv_anchor_id: str,
        context_length: int,
        model: str,
        file_size: int = 0,
    ) -> Artifact:
        """Create a KV-Cache snapshot artifact."""
        return await self.create(
            session_id=session_id,
            name=name,
            artifact_type=ArtifactType.KV_SNAPSHOT,
            file_path=file_path,
            file_size=file_size,
            kv_anchor_id=kv_anchor_id,
            context_length=context_length,
            extra_data={
                "model": model,
                "snapshot_type": "kv_cache",
            },
        )

    async def get_by_id(self, artifact_id: str) -> Optional[Artifact]:
        """Get artifact by ID."""
        query = select(Artifact).where(Artifact.id == artifact_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_session(
        self,
        session_id: str,
        artifact_type: Optional[ArtifactType] = None,
    ) -> list[Artifact]:
        """Get artifacts by session, optionally filtered by type."""
        query = select(Artifact).where(Artifact.session_id == session_id)
        
        if artifact_type:
            query = query.where(Artifact.artifact_type == artifact_type)
        
        query = query.order_by(Artifact.created_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_ppts(self, session_id: str) -> list[Artifact]:
        """Get all PPT artifacts for a session."""
        return await self.get_by_session(session_id, ArtifactType.PPT)

    async def get_documents(self, session_id: str) -> list[Artifact]:
        """Get all document artifacts for a session."""
        return await self.get_by_session(session_id, ArtifactType.DOCUMENT)

    async def get_kv_snapshots(self, session_id: str) -> list[Artifact]:
        """Get all KV-Cache snapshots for a session."""
        return await self.get_by_session(session_id, ArtifactType.KV_SNAPSHOT)

    async def get_by_parent_message(
        self,
        parent_message_id: str,
    ) -> list[Artifact]:
        """Get artifacts created by a specific message."""
        query = (
            select(Artifact)
            .where(Artifact.parent_message_id == parent_message_id)
            .order_by(Artifact.created_at.asc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        artifact_id: str,
        **updates,
    ) -> Optional[Artifact]:
        """Update artifact fields."""
        artifact = await self.get_by_id(artifact_id)
        if not artifact:
            return None

        for key, value in updates.items():
            if hasattr(artifact, key) and value is not None:
                setattr(artifact, key, value)

        await self.db.commit()
        await self.db.refresh(artifact)
        return artifact

    async def update_preview_urls(
        self,
        artifact_id: str,
        preview_url: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
    ) -> Optional[Artifact]:
        """Update artifact preview URLs (for PPT/documents)."""
        return await self.update(
            artifact_id,
            preview_url=preview_url,
            thumbnail_url=thumbnail_url,
        )

    async def delete(self, artifact_id: str) -> bool:
        """Delete an artifact (file cleanup should be handled separately)."""
        artifact = await self.get_by_id(artifact_id)
        if not artifact:
            return False

        await self.db.delete(artifact)
        await self.db.commit()
        return True

    async def delete_by_session(self, session_id: str) -> int:
        """Delete all artifacts in a session. Returns count."""
        artifacts = await self.get_by_session(session_id)
        count = len(artifacts)
        
        for artifact in artifacts:
            await self.db.delete(artifact)
        
        await self.db.commit()
        return count

    async def get_session_storage_usage(self, session_id: str) -> int:
        """Get total storage used by session artifacts in bytes."""
        artifacts = await self.get_by_session(session_id)
        return sum(artifact.file_size for artifact in artifacts)
