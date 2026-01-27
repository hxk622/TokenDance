"""Add uppercase PENDING/RUNNING/CANCELLED values to sessionstatus enum

Revision ID: e7f8g9h0i1j2
Revises: a1b2c3d4e5f6
Create Date: 2026-01-19 15:00:00.000000

This fixes a mismatch where SQLAlchemy persisted Enum names (e.g. 'PENDING')
while the previous migration added lowercase values ('pending'). Adding the
uppercase values allows inserts using Enum names to succeed.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e7f8g9h0i1j2'
down_revision: str | None = 'a1b2c3d4e5f6'
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE sessionstatus ADD VALUE IF NOT EXISTS 'PENDING'")
    op.execute("ALTER TYPE sessionstatus ADD VALUE IF NOT EXISTS 'RUNNING'")
    op.execute("ALTER TYPE sessionstatus ADD VALUE IF NOT EXISTS 'CANCELLED'")


def downgrade() -> None:
    # Removing enum values is non-trivial; leave as-is on downgrade.
    pass
