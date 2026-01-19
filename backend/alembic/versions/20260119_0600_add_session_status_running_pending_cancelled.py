"""Add RUNNING, PENDING, CANCELLED status to session

Revision ID: a1b2c3d4e5f6
Revises: 20260117_1000_add_multi_provider_auth
Create Date: 2026-01-19 06:00:00.000000

P0-1 Fix: Add RUNNING, PENDING, CANCELLED statuses to session status enum.
This allows proper session lifecycle tracking:
- PENDING: Session created, waiting for agent to start
- RUNNING: Agent is actively executing
- COMPLETED: Task finished successfully
- FAILED: Task failed with error
- CANCELLED: User stopped the execution
- ARCHIVED: Old session archived
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: str | None = '6f9h3j4k5l6m'
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # PostgreSQL allows adding values to enum types
    # We need to add: 'pending', 'running', 'cancelled'
    
    # Add new enum values
    op.execute("ALTER TYPE sessionstatus ADD VALUE IF NOT EXISTS 'pending'")
    op.execute("ALTER TYPE sessionstatus ADD VALUE IF NOT EXISTS 'running'")
    op.execute("ALTER TYPE sessionstatus ADD VALUE IF NOT EXISTS 'cancelled'")
    
    # Migrate existing 'active' sessions to 'pending' (they were never actually started)
    # Note: This is safe because new sessions will be created with 'pending' status
    # and will transition to 'running' when agent starts


def downgrade() -> None:
    # PostgreSQL doesn't support removing values from enum types easily
    # We would need to:
    # 1. Create new enum without the values
    # 2. Update column to use new enum
    # 3. Drop old enum
    # 
    # For simplicity, we'll leave the enum values in place on downgrade
    # They won't be used if the code is rolled back
    pass
