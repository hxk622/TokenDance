"""
AgentLesson Model - Agent 经验教训存储

使用 pgvector 扩展存储向量化的 Lessons，支持语义检索。
"""
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    # Fallback: 定义一个占位符类型
    Vector = None

from app.core.database import Base


class AgentLesson(Base):
    """
    Agent 经验教训表

    存储跨 session 的 Lessons，每条记录包含：
    - 标题、摘要、标签
    - 向量嵌入（用于语义检索）
    - 创建时间
    """
    __tablename__ = "agent_lessons"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    summary = Column(Text, nullable=False)
    tags = Column(JSONB, default=list)  # JSON 数组：["tag1", "tag2"]
    created_at = Column(String(50), nullable=False)  # ISO format string

    # pgvector 列（768 维 - BERT 标准）
    # 如果 pgvector 不可用，这一列将被跳过
    if PGVECTOR_AVAILABLE:
        embedding = Column(Vector(768), nullable=True)
    else:
        # Fallback: 存储为 JSON（用于开发环境）
        embedding = Column(JSONB, nullable=True)

    def __repr__(self):
        return f"<AgentLesson(id={self.id}, title='{self.title[:30]}...')>"

    def to_dict(self):
        """转为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "tags": self.tags,
            "created_at": self.created_at,
        }
