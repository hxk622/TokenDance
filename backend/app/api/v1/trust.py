"""
信任配置 API

提供工作空间信任配置的 CRUD 操作和审计日志查询。
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools.risk import OperationCategory
from app.core.database import get_db
from app.models.trust_config import TrustAuditLog
from app.services.trust_service import TrustService

router = APIRouter(prefix="/trust", tags=["trust"])


# ==================== Pydantic Schemas ====================


class TrustConfigResponse(BaseModel):
    """信任配置响应"""
    id: str
    workspace_id: str
    auto_approve_level: str
    pre_authorized_operations: list[str]
    blacklisted_operations: list[str]
    enabled: bool
    total_auto_approved: int
    total_manual_approved: int
    total_rejected: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrustConfigUpdate(BaseModel):
    """信任配置更新请求"""
    auto_approve_level: str | None = Field(
        None,
        description="自动授权的最高风险等级: none, low, medium, high"
    )
    pre_authorized_operations: list[str] | None = Field(
        None,
        description="预授权的操作类别列表"
    )
    blacklisted_operations: list[str] | None = Field(
        None,
        description="黑名单操作类别列表"
    )
    enabled: bool | None = Field(
        None,
        description="是否启用信任机制"
    )


class SessionGrantRequest(BaseModel):
    """会话授权请求"""
    operation_category: str = Field(..., description="要授权的操作类别")


class TrustAuditLogResponse(BaseModel):
    """审计日志响应"""
    id: str
    workspace_id: str
    session_id: str | None
    tool_name: str
    operation_category: str
    risk_level: str
    decision: str
    decision_reason: str | None
    operation_summary: str | None
    user_feedback: str | None
    remember_choice: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrustAuditLogList(BaseModel):
    """审计日志列表响应"""
    items: list[TrustAuditLogResponse]
    total: int
    page: int
    page_size: int


class RiskLevelInfo(BaseModel):
    """风险等级信息"""
    level: str
    description: str
    default_behavior: str


class OperationCategoryInfo(BaseModel):
    """操作类别信息"""
    category: str
    description: str
    default_risk_level: str


class TrustMetadata(BaseModel):
    """信任系统元数据"""
    risk_levels: list[RiskLevelInfo]
    operation_categories: list[OperationCategoryInfo]


# ==================== API Endpoints ====================


@router.get("/workspaces/{workspace_id}", response_model=TrustConfigResponse)
async def get_trust_config(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
) -> TrustConfigResponse:
    """获取工作空间的信任配置

    如果配置不存在，会创建默认配置。
    """
    service = TrustService(db)
    config = await service.get_or_create_trust_config(workspace_id)
    return TrustConfigResponse.model_validate(config)


@router.put("/workspaces/{workspace_id}", response_model=TrustConfigResponse)
async def update_trust_config(
    workspace_id: str,
    update_data: TrustConfigUpdate,
    db: AsyncSession = Depends(get_db),
) -> TrustConfigResponse:
    """更新工作空间的信任配置"""
    service = TrustService(db)

    try:
        config = await service.update_trust_config(
            workspace_id=workspace_id,
            auto_approve_level=update_data.auto_approve_level,
            pre_authorized_operations=update_data.pre_authorized_operations,
            blacklisted_operations=update_data.blacklisted_operations,
            enabled=update_data.enabled,
        )
        return TrustConfigResponse.model_validate(config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/sessions/{session_id}/grant")
async def grant_session_permission(
    session_id: str,
    grant_request: SessionGrantRequest,
    workspace_id: str = Query(..., description="工作空间 ID"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """授予会话级临时权限

    当用户在确认对话框中选择"记住此选择"时调用。
    """
    # 验证操作类别
    valid_categories = {c.value for c in OperationCategory}
    if grant_request.operation_category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid operation category: {grant_request.operation_category}"
        )

    service = TrustService(db)
    await service.grant_session_permission(
        workspace_id=workspace_id,
        session_id=session_id,
        operation_category=grant_request.operation_category,
    )

    return {
        "success": True,
        "message": f"Granted session permission for {grant_request.operation_category}",
        "session_id": session_id,
        "operation_category": grant_request.operation_category,
    }


@router.delete("/sessions/{session_id}/grants")
async def clear_session_grants(
    session_id: str,
    workspace_id: str = Query(..., description="工作空间 ID"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """清除会话级授权

    当会话结束时调用。
    """
    service = TrustService(db)
    await service.clear_session_grants(workspace_id, session_id)

    return {
        "success": True,
        "message": "Session grants cleared",
        "session_id": session_id,
    }


@router.get("/workspaces/{workspace_id}/audit", response_model=TrustAuditLogList)
async def get_audit_logs(
    workspace_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    session_id: str | None = Query(None, description="按会话 ID 过滤"),
    decision: str | None = Query(None, description="按决策类型过滤"),
    db: AsyncSession = Depends(get_db),
) -> TrustAuditLogList:
    """获取审计日志列表"""
    # 构建查询
    query = select(TrustAuditLog).where(
        TrustAuditLog.workspace_id == workspace_id
    )

    if session_id:
        query = query.where(TrustAuditLog.session_id == session_id)

    if decision:
        query = query.where(TrustAuditLog.decision == decision)

    # 计算总数
    count_query = select(TrustAuditLog).where(
        TrustAuditLog.workspace_id == workspace_id
    )
    if session_id:
        count_query = count_query.where(TrustAuditLog.session_id == session_id)
    if decision:
        count_query = count_query.where(TrustAuditLog.decision == decision)

    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    # 分页查询
    query = query.order_by(desc(TrustAuditLog.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    logs = result.scalars().all()

    return TrustAuditLogList(
        items=[TrustAuditLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/metadata", response_model=TrustMetadata)
async def get_trust_metadata() -> TrustMetadata:
    """获取信任系统元数据

    返回所有可用的风险等级和操作类别信息。
    """
    risk_levels = [
        RiskLevelInfo(
            level="none",
            description="无风险：纯读取操作，无任何副作用",
            default_behavior="自动执行"
        ),
        RiskLevelInfo(
            level="low",
            description="低风险：创建性操作，可能产生新文件但不修改现有内容",
            default_behavior="自动执行"
        ),
        RiskLevelInfo(
            level="medium",
            description="中风险：修改性操作，可能改变现有文件或状态",
            default_behavior="需要确认"
        ),
        RiskLevelInfo(
            level="high",
            description="高风险：危险操作，可能造成数据丢失或系统变更",
            default_behavior="需要确认"
        ),
        RiskLevelInfo(
            level="critical",
            description="极高风险：不可逆操作，始终需要用户确认",
            default_behavior="始终确认"
        ),
    ]

    operation_categories = [
        OperationCategoryInfo(
            category="web_search",
            description="网页搜索",
            default_risk_level="none"
        ),
        OperationCategoryInfo(
            category="web_read",
            description="读取网页内容",
            default_risk_level="none"
        ),
        OperationCategoryInfo(
            category="file_read",
            description="读取文件",
            default_risk_level="none"
        ),
        OperationCategoryInfo(
            category="file_create",
            description="创建新文件",
            default_risk_level="low"
        ),
        OperationCategoryInfo(
            category="file_modify",
            description="修改现有文件",
            default_risk_level="medium"
        ),
        OperationCategoryInfo(
            category="file_delete",
            description="删除文件",
            default_risk_level="medium"
        ),
        OperationCategoryInfo(
            category="shell_safe",
            description="安全 Shell 命令（ls, cat, grep 等只读命令）",
            default_risk_level="low"
        ),
        OperationCategoryInfo(
            category="shell_write",
            description="写入类 Shell 命令",
            default_risk_level="high"
        ),
        OperationCategoryInfo(
            category="shell_dangerous",
            description="危险 Shell 命令",
            default_risk_level="critical"
        ),
        OperationCategoryInfo(
            category="document_create",
            description="创建文档（Markdown, PDF 等）",
            default_risk_level="low"
        ),
    ]

    return TrustMetadata(
        risk_levels=risk_levels,
        operation_categories=operation_categories,
    )
