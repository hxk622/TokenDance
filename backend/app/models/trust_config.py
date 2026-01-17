"""
信任配置模型

用于存储工作空间级别的信任策略和审计日志。
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

if TYPE_CHECKING:
    pass


class TrustConfig(Base):
    """信任配置模型

    每个工作空间有独立的信任配置，用于控制工具调用的自动授权行为。

    核心功能：
    1. auto_approve_level: 自动授权的最高风险等级
    2. pre_authorized_operations: 预授权的操作类别列表
    3. blacklisted_operations: 黑名单操作（即使在授权等级内也需要确认）
    4. session_grants: 会话级临时授权
    """

    __tablename__ = "trust_configs"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # 关联工作空间（一对一）
    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # 信任等级设置
    # 自动授权的最高风险等级（默认 "low"，即自动执行 none 和 low 风险的操作）
    # 可选值: "none", "low", "medium", "high"（"critical" 始终需要确认）
    auto_approve_level: Mapped[str] = mapped_column(
        String(20), default="low", nullable=False
    )

    # 预授权的操作类别列表
    # 例如: ["web_search", "web_read", "file_read", "file_create"]
    # 这些操作即使超出 auto_approve_level 也会自动执行
    pre_authorized_operations: Mapped[list] = mapped_column(
        JSON, default=list, nullable=False
    )

    # 黑名单操作（即使在授权等级内也需要确认）
    # 例如: ["file_delete", "shell_dangerous"]
    blacklisted_operations: Mapped[list] = mapped_column(
        JSON, default=list, nullable=False
    )

    # 会话级临时授权
    # 格式: {session_id: {"granted_operations": ["file_modify"], "granted_at": "..."}}
    # 当用户在确认对话框中选择"记住此选择"时，会添加到这里
    session_grants: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=False
    )

    # 统计信息
    total_auto_approved: Mapped[int] = mapped_column(Integer, default=0)
    total_manual_approved: Mapped[int] = mapped_column(Integer, default=0)
    total_rejected: Mapped[int] = mapped_column(Integer, default=0)

    # 是否启用信任机制（False 则所有操作都需要确认）
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 关系（可选，取决于 Workspace 模型是否定义了反向关系）
    # workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="trust_config")

    def __repr__(self) -> str:
        return f"<TrustConfig(workspace_id={self.workspace_id}, level={self.auto_approve_level})>"

    def is_operation_blacklisted(self, operation: str) -> bool:
        """检查操作是否在黑名单中"""
        return operation in self.blacklisted_operations

    def is_operation_pre_authorized(self, operation: str) -> bool:
        """检查操作是否已预授权"""
        return operation in self.pre_authorized_operations

    def get_session_grants(self, session_id: str) -> list:
        """获取会话级授权的操作列表"""
        session_data = self.session_grants.get(session_id, {})
        return session_data.get("granted_operations", [])

    def is_session_granted(self, session_id: str, operation: str) -> bool:
        """检查操作是否已获得会话级授权"""
        return operation in self.get_session_grants(session_id)


class TrustAuditLog(Base):
    """信任审计日志

    记录所有授权决策，用于：
    1. 安全审计
    2. 用户查看历史授权记录
    3. 未来可能的信任等级自动调整
    """

    __tablename__ = "trust_audit_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    session_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # 操作信息
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    operation_category: Mapped[str] = mapped_column(String(50), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)

    # 决策信息
    # decision: "auto_approved" | "manual_approved" | "rejected" | "timeout"
    decision: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    decision_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # 操作详情（脱敏后的参数摘要）
    operation_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 用户反馈（如果有）
    user_feedback: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # 是否选择了"记住此选择"
    remember_choice: Mapped[bool] = mapped_column(Boolean, default=False)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<TrustAuditLog(tool={self.tool_name}, decision={self.decision})>"
