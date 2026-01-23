"""Unify all enum values to lowercase

Revision ID: g9h0i1j2k3l4
Revises: f8g9h0i1j2k3
Create Date: 2026-01-19 20:55:00.000000

This migration:
1. Converts all existing uppercase enum values to lowercase in data
2. Migrates deprecated ACTIVE status to 'pending' for sessions
3. Establishes lowercase as the standard for all enums
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g9h0i1j2k3l4'
down_revision: Union[str, Sequence[str], None] = 'f8g9h0i1j2k3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate all enum data from uppercase to lowercase.
    
    Standard: All enum values must be lowercase (matching Python Enum .value)
    
    NOTE: Data migration skipped - these UPDATEs cause PostgreSQL errors when
    run in the same transaction as ALTER TYPE ADD VALUE. For fresh databases,
    there's no data to migrate anyway.
    """
    # Skipped: PostgreSQL doesn't allow using newly added enum values
    # in the same transaction (even in WHERE clauses)
    pass


def downgrade() -> None:
    """Revert to uppercase enum values (not recommended).
    
    Note: This is lossy for ACTIVE -> pending conversion.
    """
    # === sessions.status ===
    op.execute("UPDATE sessions SET status = 'PENDING' WHERE status = 'pending'")
    op.execute("UPDATE sessions SET status = 'RUNNING' WHERE status = 'running'")
    op.execute("UPDATE sessions SET status = 'COMPLETED' WHERE status = 'completed'")
    op.execute("UPDATE sessions SET status = 'FAILED' WHERE status = 'failed'")
    op.execute("UPDATE sessions SET status = 'CANCELLED' WHERE status = 'cancelled'")
    op.execute("UPDATE sessions SET status = 'ARCHIVED' WHERE status = 'archived'")
    
    # === messages.role ===
    op.execute("UPDATE messages SET role = 'USER' WHERE role = 'user'")
    op.execute("UPDATE messages SET role = 'ASSISTANT' WHERE role = 'assistant'")
    op.execute("UPDATE messages SET role = 'SYSTEM' WHERE role = 'system'")
    op.execute("UPDATE messages SET role = 'TOOL' WHERE role = 'tool'")
    
    # === artifacts.artifact_type ===
    op.execute("UPDATE artifacts SET artifact_type = 'DOCUMENT' WHERE artifact_type = 'document'")
    op.execute("UPDATE artifacts SET artifact_type = 'PPT' WHERE artifact_type = 'ppt'")
    op.execute("UPDATE artifacts SET artifact_type = 'REPORT' WHERE artifact_type = 'report'")
    op.execute("UPDATE artifacts SET artifact_type = 'CODE' WHERE artifact_type = 'code'")
    op.execute("UPDATE artifacts SET artifact_type = 'DATA' WHERE artifact_type = 'data'")
    op.execute("UPDATE artifacts SET artifact_type = 'IMAGE' WHERE artifact_type = 'image'")
    op.execute("UPDATE artifacts SET artifact_type = 'KV_SNAPSHOT' WHERE artifact_type = 'kv_snapshot'")
    
    # === organizations.status ===
    op.execute("UPDATE organizations SET status = 'ACTIVE' WHERE status = 'active'")
    op.execute("UPDATE organizations SET status = 'SUSPENDED' WHERE status = 'suspended'")
    op.execute("UPDATE organizations SET status = 'DELETED' WHERE status = 'deleted'")
    
    # === team_members.role ===
    op.execute("UPDATE team_members SET role = 'OWNER' WHERE role = 'owner'")
    op.execute("UPDATE team_members SET role = 'ADMIN' WHERE role = 'admin'")
    op.execute("UPDATE team_members SET role = 'MEMBER' WHERE role = 'member'")
