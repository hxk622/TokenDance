"""Add Session, Message, Artifact, Skill tables

Revision ID: 2a5b8c9d1e3f
Revises: 1e4feadf5716
Create Date: 2026-01-12 08:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '2a5b8c9d1e3f'
down_revision: str | Sequence[str] | None = '1e4feadf5716'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create sessions table
    op.create_table('sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'COMPLETED', 'FAILED', 'ARCHIVED', name='sessionstatus'), nullable=False),
        sa.Column('skill_id', sa.String(length=100), nullable=True),
        sa.Column('context_summary', sa.Text(), nullable=True),
        sa.Column('todo_list', sa.JSON(), nullable=True),
        sa.Column('total_tokens_used', sa.Integer(), nullable=False, default=0),
        sa.Column('extra_data', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sessions_workspace_id'), 'sessions', ['workspace_id'], unique=False)

    # Create messages table
    op.create_table('messages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.Enum('USER', 'ASSISTANT', 'SYSTEM', 'TOOL', name='messagerole'), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('thinking', sa.Text(), nullable=True),
        sa.Column('tool_calls', sa.JSON(), nullable=True),
        sa.Column('tool_call_id', sa.String(length=100), nullable=True),
        sa.Column('citations', sa.JSON(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=False, default=0),
        sa.Column('full_result_ref', sa.String(length=500), nullable=True),
        sa.Column('extra_data', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_session_id'), 'messages', ['session_id'], unique=False)
    op.create_index(op.f('ix_messages_created_at'), 'messages', ['created_at'], unique=False)

    # Create artifacts table
    op.create_table('artifacts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('artifact_type', sa.Enum('DOCUMENT', 'PPT', 'REPORT', 'CODE', 'DATA', 'IMAGE', 'KV_SNAPSHOT', name='artifacttype'), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False, default=0),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('preview_url', sa.String(length=500), nullable=True),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
        sa.Column('parent_step', sa.String(length=100), nullable=True),
        sa.Column('parent_message_id', sa.String(length=36), nullable=True),
        sa.Column('kv_anchor_id', sa.String(length=100), nullable=True),
        sa.Column('context_length', sa.Integer(), nullable=True),
        sa.Column('extra_data', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_artifacts_session_id'), 'artifacts', ['session_id'], unique=False)

    # Create skills table
    op.create_table('skills',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('skill_path', sa.String(length=500), nullable=False),
        sa.Column('l1_metadata', sa.JSON(), nullable=False),
        sa.Column('l2_token_estimate', sa.Integer(), nullable=False, default=5000),
        sa.Column('has_l3_resources', sa.Boolean(), nullable=False, default=False),
        sa.Column('embedding_vector', sa.Text(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, default=0),
        sa.Column('success_rate', sa.Float(), nullable=False, default=1.0),
        sa.Column('avg_tokens_used', sa.Integer(), nullable=False, default=0),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_builtin', sa.Boolean(), nullable=False, default=False),
        sa.Column('extra_data', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('skills')
    op.drop_index(op.f('ix_artifacts_session_id'), table_name='artifacts')
    op.drop_table('artifacts')
    op.drop_index(op.f('ix_messages_created_at'), table_name='messages')
    op.drop_index(op.f('ix_messages_session_id'), table_name='messages')
    op.drop_table('messages')
    op.drop_index(op.f('ix_sessions_workspace_id'), table_name='sessions')
    op.drop_table('sessions')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS sessionstatus')
    op.execute('DROP TYPE IF EXISTS messagerole')
    op.execute('DROP TYPE IF EXISTS artifacttype')
