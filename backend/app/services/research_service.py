"""
Research Service - Business logic for deep research tasks.

Handles:
- Loading reports from MinIO when DB records exist but memory cache misses
- Converting stored JSON back to Pydantic models
- 3-tier fallback: memory → DB → MinIO
"""
import json
import logging
from datetime import datetime

from app.core.config import settings
from app.services.object_storage import get_object_storage

logger = logging.getLogger(__name__)


class ResearchService:
    """Service for managing research tasks and report loading."""

    @staticmethod
    def load_report_from_storage(task_id: str, object_key: str) -> dict | None:
        """Load research report from MinIO.

        Args:
            task_id: Research task ID
            object_key: MinIO object key (e.g., "{task_id}/report.md")

        Returns:
            Dict with report data or None if failed
        """
        storage = get_object_storage()
        if not storage:
            logger.warning("MinIO not configured, cannot load report from storage")
            return None

        try:
            bucket = settings.MINIO_BUCKET_REPORTS
            prefix = f"{task_id}"

            # Load report markdown
            report_md = storage.get_text(bucket, f"{prefix}/report.md")

            # Load metadata
            metadata_json = storage.get_text(bucket, f"{prefix}/metadata.json")
            metadata = json.loads(metadata_json)

            return {
                "task_id": task_id,
                "topic": metadata.get("topic", "Unknown Topic"),
                "report_markdown": report_md,
                "sources": [],  # Could be loaded separately if needed
                "generated_at": metadata.get("generated_at", datetime.now().isoformat()),
            }

        except Exception as e:
            logger.error(f"Failed to load report from MinIO for {task_id}: {e}")
            return None

    @staticmethod
    def load_timeline_from_storage(task_id: str) -> dict | None:
        """Load research timeline from MinIO.

        Args:
            task_id: Research task ID

        Returns:
            Timeline dict or None if failed
        """
        storage = get_object_storage()
        if not storage:
            return None

        try:
            bucket = settings.MINIO_BUCKET_REPORTS
            timeline_json = storage.get_text(bucket, f"{task_id}/timeline.json")
            return json.loads(timeline_json)
        except Exception as e:
            logger.error(f"Failed to load timeline from MinIO for {task_id}: {e}")
            return None

    @staticmethod
    def load_findings_from_storage(task_id: str) -> dict | None:
        """Load research findings from MinIO.

        Args:
            task_id: Research task ID

        Returns:
            Findings dict or None if failed
        """
        storage = get_object_storage()
        if not storage:
            return None

        try:
            bucket = settings.MINIO_BUCKET_REPORTS
            findings_json = storage.get_text(bucket, f"{task_id}/findings.json")
            return json.loads(findings_json)
        except Exception as e:
            logger.error(f"Failed to load findings from MinIO for {task_id}: {e}")
            return None
