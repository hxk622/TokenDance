"""add agent_lessons table

Revision ID: 6e9g4j5k6l7m
Revises: 5e8f2g6i7j8k
Create Date: 2026-01-16 14:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = '6e9g4j5k6l7m'
down_revision: str | Sequence[str] | None = '5e8f2g6i7j8k'
branch_labels = None
depends_on = None


def upgrade():
    """添加 agent_lessons 表，用于存储跨 session 的经验教训"""

    # 1. 跳过 pgvector 扩展（如需要可后期手动安装）
    # pgvector 需要单独安装：
    # macOS: brew install pgvector
    # 然后在 PostgreSQL 中: CREATE EXTENSION vector;

    # 2. 创建 agent_lessons 表
    op.create_table(
        'agent_lessons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('tags', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.String(length=50), nullable=False),
        # pgvector 列（768 维向量）
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. 创建索引
    op.create_index(op.f('ix_agent_lessons_id'), 'agent_lessons', ['id'], unique=False)
    op.create_index(op.f('ix_agent_lessons_title'), 'agent_lessons', ['title'], unique=False)

    # 4. 向量索引需要 pgvector 扩展，如需使用请手动创建：
    # CREATE EXTENSION IF NOT EXISTS vector;
    # CREATE INDEX agent_lessons_embedding_idx ON agent_lessons
    # USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);


def downgrade():
    """回滚"""
    op.drop_index(op.f('ix_agent_lessons_title'), table_name='agent_lessons')
    op.drop_index(op.f('ix_agent_lessons_id'), table_name='agent_lessons')

    # 删除向量索引（如果存在）
    try:
        op.execute('DROP INDEX IF EXISTS agent_lessons_embedding_idx')
    except Exception:
        pass

    op.drop_table('agent_lessons')
