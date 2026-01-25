"""
Turn Model - 对话轮次模型

Turn 是多轮对话架构的核心概念:
- 一个 Turn = User Message + Agent Execution + Assistant Response
- Turn 连接了 Conversation 和 Session
- 支持重试、分支等高级功能
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.message import Message
    from app.models.session import Session


class TurnStatus(str, Enum):
    """Turn 状态"""
    PENDING = "pending"         # 等待执行
    RUNNING = "running"         # 执行中
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"           # 失败
    CANCELLED = "cancelled"     # 已取消


class Turn(Base):
    """
    对话轮次模型

    设计理念:
    1. 原子性: 一个 Turn 是一次完整的交互单元
    2. 可追溯: 记录完整的执行过程和结果
    3. 可恢复: 支持从任意 Turn 恢复对话
    4. 可重试: 支持重试失败的 Turn

    示例:
        Turn 1: "帮我调研 AI Agent 市场" -> [Session执行] -> "好的,我来帮你调研..."
        Turn 2: "市场规模是多少?" -> [Session执行] -> "根据调研,2024年约50亿美元..."
    """
    __tablename__ = "turns"

    # 基础字段
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(26), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    turn_number = Column(Integer, nullable=False)  # 轮次序号 (从 1 开始)

    # 轮次状态
    status = Column(SQLEnum(TurnStatus), default=TurnStatus.PENDING, nullable=False, index=True)

    # 用户输入
    user_message_id = Column(String(26), ForeignKey("messages.id"), nullable=False)
    user_input = Column(String(2000), nullable=False)  # 冗余存储,便于查询

    # Agent 执行
    primary_session_id = Column(String(26), ForeignKey("sessions.id"), nullable=True)  # 主执行 Session
    skill_id = Column(String(50), nullable=True)   # 匹配的技能

    # Assistant 响应
    assistant_message_id = Column(String(26), ForeignKey("messages.id"), nullable=True)
    assistant_response = Column(String(5000), nullable=True)  # 冗余存储

    # 执行统计
    tokens_used = Column(Integer, default=0)
    duration_ms = Column(Integer, nullable=True)   # 执行时长 (毫秒)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # 关系
    conversation = relationship("Conversation", back_populates="turns")
    user_message = relationship("Message", foreign_keys=[user_message_id], post_update=True)
    assistant_message = relationship("Message", foreign_keys=[assistant_message_id], post_update=True)
    primary_session = relationship("Session", foreign_keys=[primary_session_id], post_update=True)
    # TODO: 添加 sessions 关系需要先在 Session 模型中添加 turn_id 字段

    def __repr__(self):
        return f"<Turn(id={self.id}, conversation_id={self.conversation_id}, turn_number={self.turn_number}, status={self.status})>"

    @property
    def is_pending(self) -> bool:
        """是否等待执行"""
        return self.status == TurnStatus.PENDING

    @property
    def is_running(self) -> bool:
        """是否执行中"""
        return self.status == TurnStatus.RUNNING

    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.status == TurnStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """是否失败"""
        return self.status == TurnStatus.FAILED

    def start(self):
        """开始执行"""
        self.status = TurnStatus.RUNNING
        self.started_at = datetime.utcnow()

    def complete(self, assistant_message_id: str, tokens_used: int = 0):
        """完成执行"""
        self.status = TurnStatus.COMPLETED
        self.assistant_message_id = assistant_message_id
        self.tokens_used = tokens_used
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)

    def fail(self, error_message: str = None):
        """标记为失败"""
        self.status = TurnStatus.FAILED
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)

    def cancel(self):
        """取消执行"""
        self.status = TurnStatus.CANCELLED
        self.completed_at = datetime.utcnow()

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "turn_number": self.turn_number,
            "status": self.status.value,
            "user_input": self.user_input,
            "assistant_response": self.assistant_response,
            "tokens_used": self.tokens_used,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
