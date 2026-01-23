"""
信任决策服务

负责评估工具调用是否需要用户确认，以及记录授权决策。
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import utc_now_naive

from app.agent.tools.base import BaseTool
from app.agent.tools.risk import (
    OperationCategory,
    RiskLevel,
    is_risk_within_threshold,
)
from app.models.trust_config import TrustAuditLog, TrustConfig

logger = logging.getLogger(__name__)


class TrustDecisionResult:
    """信任决策结果"""

    def __init__(
        self,
        requires_confirmation: bool,
        reason: str,
        risk_level: RiskLevel,
        operation_categories: list[OperationCategory],
        can_remember: bool = True,
    ):
        """
        Args:
            requires_confirmation: 是否需要用户确认
            reason: 决策原因（用于日志和调试）
            risk_level: 操作的风险等级
            operation_categories: 操作的类别列表
            can_remember: 是否允许用户选择"记住此选择"
        """
        self.requires_confirmation = requires_confirmation
        self.reason = reason
        self.risk_level = risk_level
        self.operation_categories = operation_categories
        # CRITICAL 风险等级不允许记住选择
        self.can_remember = can_remember and risk_level != RiskLevel.CRITICAL

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "requires_confirmation": self.requires_confirmation,
            "reason": self.reason,
            "risk_level": self.risk_level.value,
            "operation_categories": [c.value for c in self.operation_categories],
            "can_remember": self.can_remember,
        }


class TrustService:
    """信任决策服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_trust_config(self, workspace_id: str) -> TrustConfig | None:
        """获取工作空间的信任配置"""
        result = await self.db.execute(
            select(TrustConfig).where(TrustConfig.workspace_id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create_trust_config(self, workspace_id: str) -> TrustConfig:
        """获取或创建信任配置（使用默认值）

        默认配置：
        - auto_approve_level: "low" (自动执行 none 和 low 风险操作)
        - pre_authorized_operations: ["web_search", "web_read", "file_read"]
        """
        config = await self.get_trust_config(workspace_id)
        if not config:
            config = TrustConfig(
                workspace_id=workspace_id,
                auto_approve_level="low",
                pre_authorized_operations=[
                    OperationCategory.WEB_SEARCH.value,
                    OperationCategory.WEB_READ.value,
                    OperationCategory.FILE_READ.value,
                ],
                blacklisted_operations=[],
                session_grants={},
                enabled=True,
            )
            self.db.add(config)
            await self.db.commit()
            await self.db.refresh(config)
            logger.info(f"Created default trust config for workspace {workspace_id}")
        return config

    async def evaluate_trust(
        self,
        workspace_id: str,
        session_id: str,
        tool: BaseTool,
        tool_args: dict,
    ) -> TrustDecisionResult:
        """评估工具调用是否需要确认

        决策逻辑（按优先级）：
        1. 工具强制需要确认 (requires_confirmation=True) → 确认
        2. 信任机制未启用 → 确认
        3. CRITICAL 风险等级 → 始终确认
        4. 操作在黑名单中 → 确认
        5. 风险等级 ≤ auto_approve_level → 自动执行
        6. 操作类别已预授权 → 自动执行
        7. 会话级已授权 → 自动执行
        8. 其他 → 确认

        Args:
            workspace_id: 工作空间 ID
            session_id: 会话 ID
            tool: 工具实例
            tool_args: 工具调用参数

        Returns:
            TrustDecisionResult: 决策结果
        """
        # 获取动态风险等级和操作类别
        risk_level = tool.get_risk_level(**tool_args)
        operation_categories = tool.get_operation_categories(**tool_args)

        logger.debug(
            f"Evaluating trust for tool={tool.name}, "
            f"risk={risk_level.value}, categories={[c.value for c in operation_categories]}"
        )

        # 1. 工具强制需要确认
        if tool.requires_confirmation:
            return TrustDecisionResult(
                requires_confirmation=True,
                reason="工具配置为强制确认",
                risk_level=risk_level,
                operation_categories=operation_categories,
            )

        # 获取信任配置
        config = await self.get_or_create_trust_config(workspace_id)

        # 2. 信任机制未启用
        if not config.enabled:
            return TrustDecisionResult(
                requires_confirmation=True,
                reason="信任机制已禁用",
                risk_level=risk_level,
                operation_categories=operation_categories,
            )

        # 3. CRITICAL 风险等级始终需要确认
        if risk_level == RiskLevel.CRITICAL:
            return TrustDecisionResult(
                requires_confirmation=True,
                reason="极高风险操作，需要确认",
                risk_level=risk_level,
                operation_categories=operation_categories,
                can_remember=False,  # 不允许记住
            )

        # 4. 检查黑名单
        for category in operation_categories:
            if config.is_operation_blacklisted(category.value):
                return TrustDecisionResult(
                    requires_confirmation=True,
                    reason=f"操作类别 {category.value} 在黑名单中",
                    risk_level=risk_level,
                    operation_categories=operation_categories,
                )

        # 5. 检查风险等级是否在自动授权范围内
        try:
            auto_level = RiskLevel(config.auto_approve_level)
        except ValueError:
            auto_level = RiskLevel.LOW

        if is_risk_within_threshold(risk_level, auto_level):
            return TrustDecisionResult(
                requires_confirmation=False,
                reason=f"风险等级 {risk_level.value} 在自动授权范围内 (≤{auto_level.value})",
                risk_level=risk_level,
                operation_categories=operation_categories,
            )

        # 6. 检查操作类别是否已预授权
        for category in operation_categories:
            if config.is_operation_pre_authorized(category.value):
                return TrustDecisionResult(
                    requires_confirmation=False,
                    reason=f"操作类别 {category.value} 已预授权",
                    risk_level=risk_level,
                    operation_categories=operation_categories,
                )

        # 7. 检查会话级临时授权
        for category in operation_categories:
            if config.is_session_granted(session_id, category.value):
                return TrustDecisionResult(
                    requires_confirmation=False,
                    reason=f"操作类别 {category.value} 已获得会话级授权",
                    risk_level=risk_level,
                    operation_categories=operation_categories,
                )

        # 8. 默认需要确认
        return TrustDecisionResult(
            requires_confirmation=True,
            reason="操作未预授权",
            risk_level=risk_level,
            operation_categories=operation_categories,
        )

    async def grant_session_permission(
        self,
        workspace_id: str,
        session_id: str,
        operation_category: str,
    ) -> None:
        """授予会话级临时权限

        当用户在确认对话框中选择"记住此选择"时调用。

        Args:
            workspace_id: 工作空间 ID
            session_id: 会话 ID
            operation_category: 要授权的操作类别
        """
        config = await self.get_or_create_trust_config(workspace_id)

        # 复制 session_grants 以触发 SQLAlchemy 的变更检测
        session_grants = dict(config.session_grants)

        if session_id not in session_grants:
            session_grants[session_id] = {
                "granted_operations": [],
                "granted_at": utc_now_naive().isoformat(),
            }

        if operation_category not in session_grants[session_id]["granted_operations"]:
            session_grants[session_id]["granted_operations"].append(operation_category)
            logger.info(
                f"Granted session permission: workspace={workspace_id}, "
                f"session={session_id}, operation={operation_category}"
            )

        config.session_grants = session_grants
        await self.db.commit()

    async def log_decision(
        self,
        workspace_id: str,
        session_id: str,
        tool: BaseTool,
        tool_args: dict,
        decision: str,
        reason: str,
        risk_level: RiskLevel,
        operation_categories: list[OperationCategory],
        user_feedback: str | None = None,
        remember_choice: bool = False,
    ) -> TrustAuditLog:
        """记录授权决策到审计日志

        Args:
            workspace_id: 工作空间 ID
            session_id: 会话 ID
            tool: 工具实例
            tool_args: 工具调用参数
            decision: 决策结果 ("auto_approved", "manual_approved", "rejected", "timeout")
            reason: 决策原因
            risk_level: 风险等级
            operation_categories: 操作类别列表
            user_feedback: 用户反馈（可选）
            remember_choice: 是否选择了"记住此选择"

        Returns:
            TrustAuditLog: 创建的审计日志记录
        """
        # 生成操作摘要（脱敏）
        summary = self._generate_operation_summary(tool, tool_args)

        log = TrustAuditLog(
            workspace_id=workspace_id,
            session_id=session_id,
            tool_name=tool.name,
            operation_category=(
                operation_categories[0].value if operation_categories else "unknown"
            ),
            risk_level=risk_level.value,
            decision=decision,
            decision_reason=reason,
            operation_summary=summary,
            user_feedback=user_feedback,
            remember_choice=remember_choice,
        )

        self.db.add(log)

        # 更新统计信息
        config = await self.get_trust_config(workspace_id)
        if config:
            if decision == "auto_approved":
                config.total_auto_approved += 1
            elif decision == "manual_approved":
                config.total_manual_approved += 1
            elif decision in ("rejected", "timeout"):
                config.total_rejected += 1

        await self.db.commit()
        await self.db.refresh(log)

        logger.info(
            f"Logged trust decision: tool={tool.name}, decision={decision}, "
            f"risk={risk_level.value}"
        )

        return log

    async def update_trust_config(
        self,
        workspace_id: str,
        auto_approve_level: str | None = None,
        pre_authorized_operations: list[str] | None = None,
        blacklisted_operations: list[str] | None = None,
        enabled: bool | None = None,
    ) -> TrustConfig:
        """更新信任配置

        Args:
            workspace_id: 工作空间 ID
            auto_approve_level: 新的自动授权等级
            pre_authorized_operations: 新的预授权操作列表
            blacklisted_operations: 新的黑名单操作列表
            enabled: 是否启用信任机制

        Returns:
            TrustConfig: 更新后的配置
        """
        config = await self.get_or_create_trust_config(workspace_id)

        if auto_approve_level is not None:
            # 验证等级有效性
            try:
                RiskLevel(auto_approve_level)
                config.auto_approve_level = auto_approve_level
            except ValueError as e:
                raise ValueError(f"Invalid risk level: {auto_approve_level}") from e

        if pre_authorized_operations is not None:
            # 验证操作类别有效性
            valid_categories = {c.value for c in OperationCategory}
            for op in pre_authorized_operations:
                if op not in valid_categories:
                    raise ValueError(f"Invalid operation category: {op}")
            config.pre_authorized_operations = pre_authorized_operations

        if blacklisted_operations is not None:
            valid_categories = {c.value for c in OperationCategory}
            for op in blacklisted_operations:
                if op not in valid_categories:
                    raise ValueError(f"Invalid operation category: {op}")
            config.blacklisted_operations = blacklisted_operations

        if enabled is not None:
            config.enabled = enabled

        await self.db.commit()
        await self.db.refresh(config)

        logger.info(f"Updated trust config for workspace {workspace_id}")
        return config

    async def clear_session_grants(self, workspace_id: str, session_id: str) -> None:
        """清除会话级授权

        当会话结束时调用。

        Args:
            workspace_id: 工作空间 ID
            session_id: 会话 ID
        """
        config = await self.get_trust_config(workspace_id)
        if config and session_id in config.session_grants:
            session_grants = dict(config.session_grants)
            del session_grants[session_id]
            config.session_grants = session_grants
            await self.db.commit()
            logger.info(f"Cleared session grants for session {session_id}")

    def _generate_operation_summary(self, tool: BaseTool, tool_args: dict) -> str:
        """生成操作摘要（脱敏敏感信息）

        Args:
            tool: 工具实例
            tool_args: 工具调用参数

        Returns:
            str: 脱敏后的操作摘要
        """
        summary_parts = [f"Tool: {tool.name}"]

        # 只记录非敏感参数
        safe_keys = ["operation", "path", "query", "command", "url", "format"]
        for key in safe_keys:
            if key in tool_args:
                value = str(tool_args[key])
                # 截断长值
                if len(value) > 100:
                    value = value[:100] + "..."
                summary_parts.append(f"{key}: {value}")

        return " | ".join(summary_parts)
