"""Add missing lowercase enum values

Revision ID: 8a9b0c1d2e3f
Revises: 62726dc81c01
Create Date: 2026-01-24 00:05:00.000000

This migration adds lowercase enum values that were missing for:
- artifacttype
- memberrole
- orgstatus
- messagerole

These are needed because SQLAlchemy with values_callable uses .value (lowercase)
but some original migrations only created uppercase values.
"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '8a9b0c1d2e3f'
down_revision: str | Sequence[str] | None = '62726dc81c01'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add missing lowercase enum values."""
    # artifacttype
    op.execute("ALTER TYPE artifacttype ADD VALUE IF NOT EXISTS 'document'")
    op.execute("ALTER TYPE artifacttype ADD VALUE IF NOT EXISTS 'ppt'")
    op.execute("ALTER TYPE artifacttype ADD VALUE IF NOT EXISTS 'report'")
    op.execute("ALTER TYPE artifacttype ADD VALUE IF NOT EXISTS 'code'")
    op.execute("ALTER TYPE artifacttype ADD VALUE IF NOT EXISTS 'data'")
    op.execute("ALTER TYPE artifacttype ADD VALUE IF NOT EXISTS 'image'")
    op.execute("ALTER TYPE artifacttype ADD VALUE IF NOT EXISTS 'kv_snapshot'")

    # memberrole
    op.execute("ALTER TYPE memberrole ADD VALUE IF NOT EXISTS 'owner'")
    op.execute("ALTER TYPE memberrole ADD VALUE IF NOT EXISTS 'admin'")
    op.execute("ALTER TYPE memberrole ADD VALUE IF NOT EXISTS 'member'")

    # orgstatus
    op.execute("ALTER TYPE orgstatus ADD VALUE IF NOT EXISTS 'active'")
    op.execute("ALTER TYPE orgstatus ADD VALUE IF NOT EXISTS 'suspended'")
    op.execute("ALTER TYPE orgstatus ADD VALUE IF NOT EXISTS 'deleted'")

    # messagerole
    op.execute("ALTER TYPE messagerole ADD VALUE IF NOT EXISTS 'user'")
    op.execute("ALTER TYPE messagerole ADD VALUE IF NOT EXISTS 'assistant'")
    op.execute("ALTER TYPE messagerole ADD VALUE IF NOT EXISTS 'system'")
    op.execute("ALTER TYPE messagerole ADD VALUE IF NOT EXISTS 'tool'")


def downgrade() -> None:
    """PostgreSQL doesn't easily support removing enum values."""
    pass
