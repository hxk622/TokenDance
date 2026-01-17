"""Add TrustConfig and TrustAuditLog tables

Revision ID: 3b6c9d0e2f4g
Revises: 2a5b8c9d1e3f
Create Date: 2026-01-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b6c9d0e2f4g'
down_revision: Union[str, Sequence[str], None] = '3c6d9e0f2g4h'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create trust_configs table
    op.create_table('trust_configs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('auto_approve_level', sa.String(length=20), nullable=False, server_default='low'),
        sa.Column('pre_authorized_operations', sa.JSON(), nullable=False),
        sa.Column('blacklisted_operations', sa.JSON(), nullable=False),
        sa.Column('session_grants', sa.JSON(), nullable=False),
        sa.Column('total_auto_approved', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_manual_approved', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_rejected', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', name='uq_trust_config_workspace')
    )
    op.create_index(op.f('ix_trust_configs_workspace_id'), 'trust_configs', ['workspace_id'], unique=True)

    # Create trust_audit_logs table
    op.create_table('trust_audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=True),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('operation_category', sa.String(length=50), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('decision', sa.String(length=20), nullable=False),
        sa.Column('decision_reason', sa.String(length=500), nullable=True),
        sa.Column('operation_summary', sa.Text(), nullable=True),
        sa.Column('user_feedback', sa.String(length=500), nullable=True),
        sa.Column('remember_choice', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trust_audit_logs_workspace_id'), 'trust_audit_logs', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_trust_audit_logs_session_id'), 'trust_audit_logs', ['session_id'], unique=False)
    op.create_index(op.f('ix_trust_audit_logs_decision'), 'trust_audit_logs', ['decision'], unique=False)
    op.create_index(op.f('ix_trust_audit_logs_created_at'), 'trust_audit_logs', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop trust_audit_logs table
    op.drop_index(op.f('ix_trust_audit_logs_created_at'), table_name='trust_audit_logs')
    op.drop_index(op.f('ix_trust_audit_logs_decision'), table_name='trust_audit_logs')
    op.drop_index(op.f('ix_trust_audit_logs_session_id'), table_name='trust_audit_logs')
    op.drop_index(op.f('ix_trust_audit_logs_workspace_id'), table_name='trust_audit_logs')
    op.drop_table('trust_audit_logs')

    # Drop trust_configs table
    op.drop_index(op.f('ix_trust_configs_workspace_id'), table_name='trust_configs')
    op.drop_table('trust_configs')
