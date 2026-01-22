"""
Artifact API endpoints.

Provides endpoints for accessing and downloading artifacts.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_permission_service
from app.core.logging import get_logger
from app.models.artifact import ArtifactType
from app.models.user import User
from app.repositories.artifact_repository import ArtifactRepository
from app.schemas.artifact import ArtifactResponse
from app.services.object_storage import get_object_storage
from app.services.permission_service import PermissionError, PermissionService

logger = get_logger(__name__)
router = APIRouter()


def get_artifact_repo(db: AsyncSession = Depends(get_db)) -> ArtifactRepository:
    """Dependency to get ArtifactRepository instance."""
    return ArtifactRepository(db)


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: str,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    artifact_repo: ArtifactRepository = Depends(get_artifact_repo),
):
    """Get artifact metadata by ID."""
    artifact = await artifact_repo.get_by_id(artifact_id)

    if not artifact:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Artifact {artifact_id} not found",
        )

    # Check permission via session access
    if artifact.session_id:
        try:
            await permission_service.check_session_access(current_user, artifact.session_id)
        except PermissionError as e:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail=str(e),
            ) from e

    return ArtifactResponse.model_validate(artifact)


@router.get("/{artifact_id}/download")
async def download_artifact(
    artifact_id: str,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    artifact_repo: ArtifactRepository = Depends(get_artifact_repo),
    settings: Settings = Depends(get_settings),
):
    """
    Download artifact content.

    Supports multiple storage backends:
    - minio:// - MinIO object storage
    - local:// - Local filesystem
    """
    artifact = await artifact_repo.get_by_id(artifact_id)

    if not artifact:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Artifact {artifact_id} not found",
        )

    # Check permission via session access
    if artifact.session_id:
        try:
            await permission_service.check_session_access(current_user, artifact.session_id)
        except PermissionError as e:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail=str(e),
            ) from e

    file_path = artifact.file_path
    mime_type = artifact.mime_type or "application/octet-stream"

    # Determine download filename
    filename = artifact.name
    if not filename.endswith(artifact.get_file_extension()):
        ext = _get_extension_for_type(artifact.artifact_type, artifact.mime_type)
        if ext:
            filename = f"{filename}{ext}"

    # Handle different storage backends
    if file_path.startswith("minio://"):
        # MinIO storage
        return await _download_from_minio(file_path, filename, mime_type)

    elif file_path.startswith("local://"):
        # Local filesystem
        return _download_from_local(file_path, filename, mime_type, settings)

    else:
        # Legacy: assume it's a relative path under sessions data
        full_path = Path(settings.SESSIONS_DATA_PATH) / file_path
        if not full_path.exists():
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Artifact file not found on storage",
            )
        return FileResponse(
            path=str(full_path),
            filename=filename,
            media_type=mime_type,
        )


@router.get("/{artifact_id}/preview")
async def get_artifact_preview(
    artifact_id: str,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    artifact_repo: ArtifactRepository = Depends(get_artifact_repo),
):
    """
    Get artifact content preview.

    Returns a truncated preview of the artifact content for quick display.
    """
    artifact = await artifact_repo.get_by_id(artifact_id)

    if not artifact:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Artifact {artifact_id} not found",
        )

    # Check permission via session access
    if artifact.session_id:
        try:
            await permission_service.check_session_access(current_user, artifact.session_id)
        except PermissionError as e:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail=str(e),
            ) from e

    return {
        "artifact_id": artifact.id,
        "name": artifact.name,
        "type": artifact.artifact_type.value,
        "preview": artifact.content_preview,
        "word_count": artifact.word_count,
        "file_size": artifact.file_size,
    }


async def _download_from_minio(file_path: str, filename: str, mime_type: str):
    """Download file from MinIO storage."""
    storage = get_object_storage()

    if not storage:
        raise HTTPException(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Object storage not configured",
        )

    # Parse minio://bucket/key format
    # Example: minio://tokendance-artifacts/sessions/xxx/findings.md
    path_parts = file_path.replace("minio://", "").split("/", 1)
    if len(path_parts) != 2:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Invalid MinIO path format",
        )

    bucket, object_key = path_parts

    try:
        # Get presigned URL for download (valid for 1 hour)
        presigned_url = storage.presigned_get_url(bucket, object_key, expires_seconds=3600)

        # Redirect to presigned URL
        return Response(
            status_code=http_status.HTTP_307_TEMPORARY_REDIRECT,
            headers={
                "Location": presigned_url,
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    except Exception as e:
        logger.error(f"MinIO download failed: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download from storage: {str(e)}",
        ) from e


def _download_from_local(file_path: str, filename: str, mime_type: str, settings: Settings):
    """Download file from local filesystem."""
    # Parse local://path format
    actual_path = file_path.replace("local://", "")

    # Security check: ensure path is within allowed directories
    full_path = Path(actual_path)
    sessions_path = Path(settings.SESSIONS_DATA_PATH).resolve()

    try:
        resolved_path = full_path.resolve()
        # Allow paths under sessions data path
        if not str(resolved_path).startswith(str(sessions_path)):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Access to this path is not allowed",
            )
    except HTTPException:
        raise  # Re-raise HTTPException as-is
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Invalid file path",
        ) from e

    if not full_path.exists():
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Artifact file not found on storage",
        )

    return FileResponse(
        path=str(full_path),
        filename=filename,
        media_type=mime_type,
    )


def _get_extension_for_type(artifact_type: ArtifactType, mime_type: str | None) -> str:
    """Get appropriate file extension based on artifact type and mime type."""
    type_extensions = {
        ArtifactType.DOCUMENT: ".md",
        ArtifactType.REPORT: ".md",
        ArtifactType.PPT: ".pptx",
        ArtifactType.CODE: ".py",
        ArtifactType.DATA: ".json",
        ArtifactType.IMAGE: ".png",
    }

    mime_extensions = {
        "text/markdown": ".md",
        "text/plain": ".txt",
        "application/json": ".json",
        "application/pdf": ".pdf",
        "image/png": ".png",
        "image/jpeg": ".jpg",
    }

    if mime_type and mime_type in mime_extensions:
        return mime_extensions[mime_type]

    return type_extensions.get(artifact_type, "")
