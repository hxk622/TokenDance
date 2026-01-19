"""
Object Storage Service (MinIO/S3 compatible)

- Thin wrapper around MinIO Python client
- Safe no-op when not configured
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import timedelta
from io import BytesIO
from typing import Any

from ..core.config import settings

logger = logging.getLogger(__name__)

try:
    from minio import Minio
    from minio.error import S3Error
except Exception:  # pragma: no cover - allow import even if dependency missing
    Minio = None  # type: ignore
    S3Error = Exception  # type: ignore


@dataclass
class ObjectStorageConfig:
    endpoint: str
    access_key: str
    secret_key: str
    secure: bool = False
    region: str | None = None


class ObjectStorageClient:
    def __init__(self, cfg: ObjectStorageConfig):
        if Minio is None:
            raise RuntimeError("minio client not installed")

        self._client = Minio(
            endpoint=cfg.endpoint,
            access_key=cfg.access_key,
            secret_key=cfg.secret_key,
            secure=cfg.secure,
            region=cfg.region,
        )

    def ensure_bucket(self, bucket: str) -> None:
        try:
            if not self._client.bucket_exists(bucket):
                self._client.make_bucket(bucket)
        except S3Error as e:  # bucket may already exist in race
            if getattr(e, "code", "") != "BucketAlreadyOwnedByYou":
                raise

    def put_text(self, bucket: str, key: str, text: str, content_type: str = "text/plain; charset=utf-8") -> None:
        data = text.encode("utf-8")
        self._client.put_object(
            bucket,
            key,
            data=BytesIO(data),
            length=len(data),
            content_type=content_type,
        )

    def put_json(self, bucket: str, key: str, obj: Any) -> None:
        content = json.dumps(obj, ensure_ascii=False, indent=2)
        self.put_text(bucket, key, content, content_type="application/json; charset=utf-8")

    def put_bytes(self, bucket: str, key: str, blob: bytes, content_type: str) -> None:
        self._client.put_object(
            bucket,
            key,
            data=BytesIO(blob),
            length=len(blob),
            content_type=content_type,
        )

    def get_text(self, bucket: str, key: str) -> str:
        resp = self._client.get_object(bucket, key)
        try:
            return resp.read().decode("utf-8")
        finally:
            resp.close()
            resp.release_conn()

    def presigned_get_url(self, bucket: str, key: str, expires_seconds: int = 3600) -> str:
        return self._client.presigned_get_object(bucket, key, expires=timedelta(seconds=expires_seconds))


_storage_singleton: ObjectStorageClient | None = None


def get_object_storage() -> ObjectStorageClient | None:
    """Return configured object storage client or None if not configured."""
    global _storage_singleton

    if _storage_singleton is not None:
        return _storage_singleton

    # Guard: configuration must be present
    if not (settings.MINIO_ENDPOINT and settings.MINIO_ACCESS_KEY and settings.MINIO_SECRET_KEY):
        logger.info("MinIO not configured; object storage disabled")
        return None

    try:
        cfg = ObjectStorageConfig(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=bool(settings.MINIO_SECURE),
            region=settings.MINIO_REGION,
        )
        _storage_singleton = ObjectStorageClient(cfg)
        logger.info("MinIO client initialized")
        return _storage_singleton
    except Exception as e:  # pragma: no cover
        logger.warning(f"Failed to initialize MinIO client: {e}")
        return None
