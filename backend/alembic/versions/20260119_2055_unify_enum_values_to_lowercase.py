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
    """
    # === sessions.status ===
    # Convert uppercase to lowercase
    op.execute("UPDATE sessions SET status = 'pending' WHERE status = 'PENDING'")
    op.execute("UPDATE sessions SET status = 'running' WHERE status = 'RUNNING'")
    op.execute("UPDATE sessions SET status = 'completed' WHERE status = 'COMPLETED'")
    op.execute("UPDATE sessions SET status = 'failed' WHERE status = 'FAILED'")
    op.execute("UPDATE sessions SET status = 'cancelled' WHERE status = 'CANCELLED'")
    op.execute("UPDATE sessions SET status = 'archived' WHERE status = 'ARCHIVED'")
    # Migrate deprecated ACTIVE -> pending (ACTIVE was old status before PENDING/RUNNING split)
    op.execute("UPDATE sessions SET status = 'pending' WHERE status = 'ACTIVE'")
    op.execute("UPDATE sessions SET status = 'pending' WHERE status = 'active'")
    
    # === messages.role ===
    op.execute("UPDATE messages SET role = 'user' WHERE role = 'USER'")
    op.execute("UPDATE messages SET role = 'assistant' WHERE role = 'ASSISTANT'")
    op.execute("UPDATE messages SET role = 'system' WHERE role = 'SYSTEM'")
    op.execute("UPDATE messages SET role = 'tool' WHERE role = 'TOOL'")
    
    # === artifacts.artifact_type ===
    op.execute("UPDATE artifacts SET artifact_type = 'document' WHERE artifact_type = 'DOCUMENT'")
    op.execute("UPDATE artifacts SET artifact_type = 'ppt' WHERE artifact_type = 'PPT'")
    op.execute("UPDATE artifacts SET artifact_type = 'report' WHERE artifact_type = 'REPORT'")
    op.execute("UPDATE artifacts SET artifact_type = 'code' WHERE artifact_type = 'CODE'")
    op.execute("UPDATE artifacts SET artifact_type = 'data' WHERE artifact_type = 'DATA'")
    op.execute("UPDATE artifacts SET artifact_type = 'image' WHERE artifact_type = 'IMAGE'")
    op.execute("UPDATE artifacts SET artifact_type = 'kv_snapshot' WHERE artifact_type = 'KV_SNAPSHOT'")
    
    # === organizations.status ===
    op.execute("UPDATE organizations SET status = 'active' WHERE status = 'ACTIVE'")
    op.execute("UPDATE organizations SET status = 'suspended' WHERE status = 'SUSPENDED'")
    op.execute("UPDATE organizations SET status = 'deleted' WHERE status = 'DELETED'")
    
    # === team_members.role ===
    op.execute("UPDATE team_members SET role = 'owner' WHERE role = 'OWNER'")
    op.execute("UPDATE team_members SET role = 'admin' WHERE role = 'ADMIN'")
    op.execute("UPDATE team_members SET role = 'member' WHERE role = 'MEMBER'")


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
