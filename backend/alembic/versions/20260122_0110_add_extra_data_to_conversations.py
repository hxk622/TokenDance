"""Add extra_data to conversations table

Revision ID: 77bdc89bcb30
Revises: 66425cd35564
Create Date: 2026-01-22 01:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77bdc89bcb30'
down_revision: Union[str, Sequence[str], None] = '66425cd35564'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add extra_data column to conversations table."""
    op.add_column(
        'conversations',
        sa.Column('extra_data', sa.JSON(), nullable=False, server_default='{}')
    )


def downgrade() -> None:
    """Remove extra_data column from conversations table."""
    op.drop_column('conversations', 'extra_data')
