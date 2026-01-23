"""merge_migration_heads

Revision ID: 62726dc81c01
Revises: 77bdc89bcb30, 5e8f1g2h3i4j
Create Date: 2026-01-23 23:59:01.706500

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '62726dc81c01'
down_revision: Union[str, Sequence[str], None] = ('77bdc89bcb30', '5e8f1g2h3i4j')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
