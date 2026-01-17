"""Add AgentConfig, LLMProvider, LLMModel tables

Revision ID: 4d7e0f1h5i6j
Revises: 3c6d9e0f2g4h
Create Date: 2026-01-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d7e0f1h5i6j'
down_revision: Union[str, Sequence[str], None] = '3b6c9d0e2f4g'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    # Create llm_providers table
    op.create_table('llm_providers',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('api_base_url', sa.String(length=255), nullable=True),
        sa.Column('requires_api_key', sa.Boolean(), nullable=False, default=True),
        sa.Column('supported_models', sa.JSON(), nullable=False, default=list),
        sa.Column('supports_streaming', sa.Boolean(), nullable=False, default=True),
        sa.Column('supports_tools', sa.Boolean(), nullable=False, default=True),
        sa.Column('supports_vision', sa.Boolean(), nullable=False, default=False),
        sa.Column('max_context_tokens', sa.Integer(), nullable=True),
        sa.Column('input_price_per_1m', sa.Float(), nullable=True),
        sa.Column('output_price_per_1m', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_builtin', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_llm_providers_name'), 'llm_providers', ['name'], unique=True)
    
    # Create llm_models table
    op.create_table('llm_models',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('provider_id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('max_tokens', sa.Integer(), nullable=False),
        sa.Column('max_context_tokens', sa.Integer(), nullable=False),
        sa.Column('supports_streaming', sa.Boolean(), nullable=False, default=True),
        sa.Column('supports_tools', sa.Boolean(), nullable=False, default=True),
        sa.Column('supports_vision', sa.Boolean(), nullable=False, default=False),
        sa.Column('input_price_per_1m', sa.Float(), nullable=True),
        sa.Column('output_price_per_1m', sa.Float(), nullable=True),
        sa.Column('recommended_temperature', sa.Float(), nullable=False, default=1.0),
        sa.Column('recommended_max_tokens', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.ForeignKeyConstraint(['provider_id'], ['llm_providers.id'], )
    )
    op.create_index(op.f('ix_llm_models_provider_id'), 'llm_models', ['provider_id'], unique=False)
    op.create_index(op.f('ix_llm_models_name'), 'llm_models', ['name'], unique=True)
    
    # Create agent_configs table
    op.create_table('agent_configs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('llm_provider', sa.String(length=50), nullable=False, default='anthropic'),
        sa.Column('llm_model', sa.String(length=100), nullable=False, default='claude-3-5-sonnet-20241022'),
        sa.Column('llm_max_tokens', sa.Integer(), nullable=False, default=8192),
        sa.Column('llm_temperature', sa.Float(), nullable=False, default=1.0),
        sa.Column('llm_top_p', sa.Float(), nullable=True),
        sa.Column('llm_top_k', sa.Integer(), nullable=True),
        sa.Column('max_iterations', sa.Integer(), nullable=False, default=20),
        sa.Column('enable_skills', sa.Boolean(), nullable=False, default=True),
        sa.Column('enable_hybrid_execution', sa.Boolean(), nullable=False, default=True),
        sa.Column('enabled_tools', sa.JSON(), nullable=True, default=list),
        sa.Column('tool_risk_threshold', sa.String(length=20), nullable=False, default='MEDIUM'),
        sa.Column('enable_working_memory', sa.Boolean(), nullable=False, default=True),
        sa.Column('enable_long_memory', sa.Boolean(), nullable=False, default=False),
        sa.Column('memory_retention_days', sa.Integer(), nullable=True, default=30),
        sa.Column('custom_system_prompt', sa.Text(), nullable=True),
        sa.Column('additional_context', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True, default=dict),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('updated_by', sa.String(length=36), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], )
    )
    op.create_index(op.f('ix_agent_configs_workspace_id'), 'agent_configs', ['workspace_id'], unique=False)
    
    # Add agent_config_id column to sessions table
    op.add_column('sessions',
        sa.Column('agent_config_id', sa.String(length=36), nullable=True)
    )
    op.create_foreign_key(
        'fk_sessions_agent_config_id',
        'sessions', 'agent_configs',
        ['agent_config_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index(op.f('ix_sessions_agent_config_id'), 'sessions', ['agent_config_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    
    # Remove agent_config_id from sessions
    op.drop_index(op.f('ix_sessions_agent_config_id'), table_name='sessions')
    op.drop_constraint('fk_sessions_agent_config_id', 'sessions', type_='foreignkey')
    op.drop_column('sessions', 'agent_config_id')
    
    # Drop agent_configs table
    op.drop_index(op.f('ix_agent_configs_workspace_id'), table_name='agent_configs')
    op.drop_table('agent_configs')
    
    # Drop llm_models table
    op.drop_index(op.f('ix_llm_models_name'), table_name='llm_models')
    op.drop_index(op.f('ix_llm_models_provider_id'), table_name='llm_models')
    op.drop_table('llm_models')
    
    # Drop llm_providers table
    op.drop_index(op.f('ix_llm_providers_name'), table_name='llm_providers')
    op.drop_table('llm_providers')
