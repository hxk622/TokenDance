"""Add Organization, Team, TeamMember tables for multi-tenancy

Revision ID: 3c6d9e0f2g4h
Revises: 2a5b8c9d1e3f
Create Date: 2026-01-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c6d9e0f2g4h'
down_revision: Union[str, Sequence[str], None] = '2a5b8c9d1e3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create organizations table
    op.create_table('organizations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'SUSPENDED', 'DELETED', name='orgstatus'), nullable=False),
        sa.Column('settings', sa.JSON(), nullable=False),
        sa.Column('max_teams', sa.Integer(), nullable=False, default=10),
        sa.Column('max_workspaces', sa.Integer(), nullable=False, default=100),
        sa.Column('max_sessions', sa.Integer(), nullable=False, default=1000),
        sa.Column('storage_quota_gb', sa.Integer(), nullable=False, default=100),
        sa.Column('current_teams', sa.Integer(), nullable=False, default=0),
        sa.Column('current_workspaces', sa.Integer(), nullable=False, default=0),
        sa.Column('current_sessions', sa.Integer(), nullable=False, default=0),
        sa.Column('storage_used_gb', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_organizations_slug'), 'organizations', ['slug'], unique=True)

    # Create teams table
    op.create_table('teams',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('org_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('org_id', 'slug', name='uq_team_slug')
    )
    op.create_index(op.f('ix_teams_org_id'), 'teams', ['org_id'], unique=False)

    # Create team_members table
    op.create_table('team_members',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('team_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.Enum('OWNER', 'ADMIN', 'MEMBER', name='memberrole'), nullable=False),
        sa.Column('permissions', sa.JSON(), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('team_id', 'user_id', name='uq_team_member')
    )
    op.create_index(op.f('ix_team_members_team_id'), 'team_members', ['team_id'], unique=False)
    op.create_index(op.f('ix_team_members_user_id'), 'team_members', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_team_members_user_id'), table_name='team_members')
    op.drop_index(op.f('ix_team_members_team_id'), table_name='team_members')
    op.drop_table('team_members')
    op.drop_index(op.f('ix_teams_org_id'), table_name='teams')
    op.drop_table('teams')
    op.drop_index(op.f('ix_organizations_slug'), table_name='organizations')
    op.drop_table('organizations')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS orgstatus')
    op.execute('DROP TYPE IF EXISTS memberrole')
