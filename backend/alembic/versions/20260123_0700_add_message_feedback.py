"""Add feedback columns to messages table

Revision ID: 3b6c9d0e2f4g
Revises: 5d7e8f9a0b1c
Create Date: 2026-01-23 07:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5e8f1g2h3i4j'
down_revision: str | Sequence[str] | None = '4d7e0f1h5i6j'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add feedback and feedback_at columns to messages table."""
    # Create feedback type enum
    feedback_type = sa.Enum('like', 'dislike', name='feedbacktype')
    feedback_type.create(op.get_bind(), checkfirst=True)

    # Add feedback column
    op.add_column('messages', sa.Column(
        'feedback',
        sa.Enum('like', 'dislike', name='feedbacktype'),
        nullable=True
    ))

    # Add feedback_at column
    op.add_column('messages', sa.Column(
        'feedback_at',
        sa.DateTime(),
        nullable=True
    ))


def downgrade() -> None:
    """Remove feedback columns from messages table."""
    op.drop_column('messages', 'feedback_at')
    op.drop_column('messages', 'feedback')

    # Drop the enum type
    op.execute('DROP TYPE IF EXISTS feedbacktype')
