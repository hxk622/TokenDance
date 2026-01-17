"""Add AgentState and AgentCheckpoint tables for state persistence

Revision ID: 5e8f2g6i7j8k
Revises: 4d7e0f1h5i6j
Create Date: 2026-01-16 14:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5e8f2g6i7j8k'
down_revision: str | Sequence[str] | None = '4d7e0f1h5i6j'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    # Create agent_states table
    op.create_table('agent_states',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('agent_config_id', sa.String(length=36), nullable=True),
        sa.Column('current_state', sa.String(length=50), nullable=False, default='IDLE'),
        sa.Column('iteration_count', sa.Integer(), nullable=False, default=0),
        sa.Column('input_tokens_used', sa.Integer(), nullable=False, default=0),
        sa.Column('output_tokens_used', sa.Integer(), nullable=False, default=0),
        sa.Column('total_tokens_used', sa.Integer(), nullable=False, default=0),
        sa.Column('tool_calls_count', sa.Integer(), nullable=False, default=0),
        sa.Column('tool_calls_success', sa.Integer(), nullable=False, default=0),
        sa.Column('tool_calls_failed', sa.Integer(), nullable=False, default=0),
        sa.Column('error_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('last_error_time', sa.DateTime(), nullable=True),
        sa.Column('average_iteration_time', sa.Float(), nullable=True),
        sa.Column('total_execution_time', sa.Float(), nullable=True),
        sa.Column('state_data', sa.JSON(), nullable=True, default=dict),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_config_id'], ['agent_configs.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('session_id')
    )
    op.create_index(op.f('ix_agent_states_session_id'), 'agent_states', ['session_id'], unique=True)
    op.create_index(op.f('ix_agent_states_agent_config_id'), 'agent_states', ['agent_config_id'], unique=False)

    # Create agent_checkpoints table
    op.create_table('agent_checkpoints',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('agent_state_id', sa.String(length=36), nullable=False),
        sa.Column('iteration', sa.Integer(), nullable=False),
        sa.Column('checkpoint_type', sa.String(length=50), nullable=False),
        sa.Column('context_snapshot', sa.JSON(), nullable=True),
        sa.Column('working_memory_snapshot', sa.JSON(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True, default=dict),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agent_state_id'], ['agent_states.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_agent_checkpoints_agent_state_id'), 'agent_checkpoints', ['agent_state_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""

    # Drop agent_checkpoints table
    op.drop_index(op.f('ix_agent_checkpoints_agent_state_id'), table_name='agent_checkpoints')
    op.drop_table('agent_checkpoints')

    # Drop agent_states table
    op.drop_index(op.f('ix_agent_states_agent_config_id'), table_name='agent_states')
    op.drop_index(op.f('ix_agent_states_session_id'), table_name='agent_states')
    op.drop_table('agent_states')
