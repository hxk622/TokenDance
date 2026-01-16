"""add agent_lessons table

Revision ID: 20260116_1400
Revises: 20260116_1000
Create Date: 2026-01-16 14:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260116_1400'
down_revision = '20260116_1000'
branch_labels = None
depends_on = None


def upgrade():
    """添加 agent_lessons 表，用于存储跨 session 的经验教训"""
    
    # 1. 启用 pgvector 扩展（如果未启用）
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
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
    
    # 4. 创建向量索引（使用 HNSW 算法 - 更快的 ANN 搜索）
    # 注意：这需要 pgvector 扩展支持
    try:
        op.execute(
            """
            CREATE INDEX agent_lessons_embedding_idx 
            ON agent_lessons 
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
            """
        )
    except Exception as e:
        # 如果 pgvector 不可用，跳过向量索引创建
        print(f"Warning: Could not create vector index: {e}")


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
