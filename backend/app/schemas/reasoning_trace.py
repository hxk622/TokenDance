"""
ReasoningTrace Schemas - 推理轨迹数据模型

用于记录和展示 AI 的决策过程，提高透明度和用户信任。
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ResearchPhase(str, Enum):
    """研究阶段"""
    PLANNING = "planning"         # 规划查询
    SEARCHING = "searching"       # 搜索中
    READING = "reading"           # 阅读来源
    ANALYZING = "analyzing"       # 分析内容
    VERIFYING = "verifying"       # 交叉验证
    SYNTHESIZING = "synthesizing" # 综合报告


class ReasoningAction(str, Enum):
    """推理动作类型"""
    EXPAND_QUERY = "expand_query"         # 扩展搜索词
    SELECT_SOURCE = "select_source"       # 选择来源
    SKIP_SOURCE = "skip_source"           # 跳过来源
    DEEP_DIVE = "deep_dive"               # 深入研究
    CROSS_VERIFY = "cross_verify"         # 交叉验证
    DETECT_CONTRADICTION = "detect_contradiction"  # 检测矛盾
    CONCLUDE = "conclude"                 # 得出结论
    ADJUST_DEPTH = "adjust_depth"         # 调整深度


class ReasoningEvidence(BaseModel):
    """支撑证据"""
    source: str = Field(..., description="来源 (URL 或描述)")
    content: str = Field(..., description="证据内容摘要")
    relevance: float = Field(default=0.8, ge=0, le=1, description="相关度 0-1")


class ReasoningAlternative(BaseModel):
    """备选方案"""
    description: str = Field(..., description="方案描述")
    reason_rejected: str = Field(..., description="放弃原因")


class ReasoningTrace(BaseModel):
    """单条推理轨迹"""
    id: str = Field(..., description="唯一标识")
    timestamp: datetime = Field(default_factory=datetime.now)
    phase: ResearchPhase = Field(..., description="当前研究阶段")
    action: ReasoningAction = Field(..., description="决策动作")
    reasoning: str = Field(..., description="人话解释决策原因")
    confidence: float = Field(default=0.8, ge=0, le=1, description="决策置信度")
    alternatives: list[ReasoningAlternative] = Field(
        default_factory=list, description="被放弃的备选方案"
    )
    evidence: list[ReasoningEvidence] = Field(
        default_factory=list, description="支撑决策的证据"
    )
    metadata: dict = Field(default_factory=dict, description="额外元数据")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ReasoningTraceCreate(BaseModel):
    """创建推理轨迹的请求"""
    phase: ResearchPhase
    action: ReasoningAction
    reasoning: str
    confidence: float = 0.8
    alternatives: list[ReasoningAlternative] = Field(default_factory=list)
    evidence: list[ReasoningEvidence] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class ReasoningTraceFeedback(BaseModel):
    """用户对推理的反馈"""
    trace_id: str
    feedback: str = Field(..., description="positive 或 negative")
    comment: str | None = None


class ReasoningTraceList(BaseModel):
    """推理轨迹列表响应"""
    traces: list[ReasoningTrace]
    total: int
    session_id: str
