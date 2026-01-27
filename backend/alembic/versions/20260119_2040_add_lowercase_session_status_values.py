"""Add lowercase values to sessionstatus enum

Revision ID: f8g9h0i1j2k3
Revises: e4929bd393e9
Create Date: 2026-01-19 20:40:00.000000

This fixes the mismatch where SQLAlchemy (with values_callable) uses
lowercase Enum values (e.g. 'completed') but the database only has
uppercase values ('COMPLETED') for the original status values.
"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f8g9h0i1j2k3'
down_revision: str | Sequence[str] | None = 'e4929bd393e9'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add missing lowercase enum values for sessionstatus.

    The original migration created: ACTIVE, COMPLETED, FAILED, ARCHIVED (uppercase)
    Later migrations added: pending, running, cancelled (lowercase)

    SQLAlchemy with values_callable uses .value (lowercase), so we need:
    completed, failed, active, archived
    """
    op.execute("ALTER TYPE sessionstatus ADD VALUE IF NOT EXISTS 'completed'")
    op.execute("ALTER TYPE sessionstatus ADD VALUE IF NOT EXISTS 'failed'")
    op.execute("ALTER TYPE sessionstatus ADD VALUE IF NOT EXISTS 'active'")
    op.execute("ALTER TYPE sessionstatus ADD VALUE IF NOT EXISTS 'archived'")


def downgrade() -> None:
    # PostgreSQL doesn't easily support removing enum values
    # Leave them in place on downgrade
    pass
