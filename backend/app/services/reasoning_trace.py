"""
ReasoningTraceService - 推理轨迹服务

记录和管理 AI 的决策过程，用于：
1. 向用户展示 AI 的思考过程 (透明化)
2. 收集用户反馈用于改进 (学习)
3. 调试和审计 AI 决策 (可追溯)
"""
import logging
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime

from app.agent.types import SSEEvent, SSEEventType
from app.schemas.reasoning_trace import (
    ReasoningAction,
    ReasoningAlternative,
    ReasoningEvidence,
    ReasoningTrace,
    ReasoningTraceFeedback,
    ResearchPhase,
)

logger = logging.getLogger(__name__)


class ReasoningTraceService:
    """推理轨迹服务

    负责记录、存储和检索 AI 的推理过程。
    支持流式推送和用户反馈收集。
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._traces: list[ReasoningTrace] = []
        self._feedback: dict[str, ReasoningTraceFeedback] = {}

    def record_decision(
        self,
        phase: ResearchPhase,
        action: ReasoningAction,
        reasoning: str,
        confidence: float = 0.8,
        alternatives: list[dict] | None = None,
        evidence: list[dict] | None = None,
        metadata: dict | None = None,
    ) -> ReasoningTrace:
        """记录一个决策点

        Args:
            phase: 当前研究阶段
            action: 决策动作类型
            reasoning: 人话解释 (给用户看的)
            confidence: 决策置信度 0-1
            alternatives: 被放弃的备选方案列表
            evidence: 支撑决策的证据列表
            metadata: 额外元数据

        Returns:
            创建的 ReasoningTrace 对象
        """
        trace_id = str(uuid.uuid4())[:8]

        # 转换备选方案
        alt_list = []
        if alternatives:
            for alt in alternatives:
                alt_list.append(ReasoningAlternative(
                    description=alt.get("description", ""),
                    reason_rejected=alt.get("reason_rejected", alt.get("reason", ""))
                ))

        # 转换证据
        ev_list = []
        if evidence:
            for ev in evidence:
                ev_list.append(ReasoningEvidence(
                    source=ev.get("source", ""),
                    content=ev.get("content", ""),
                    relevance=ev.get("relevance", 0.8)
                ))

        trace = ReasoningTrace(
            id=trace_id,
            timestamp=datetime.now(),
            phase=phase,
            action=action,
            reasoning=reasoning,
            confidence=confidence,
            alternatives=alt_list,
            evidence=ev_list,
            metadata=metadata or {}
        )

        self._traces.append(trace)
        logger.info(f"[ReasoningTrace] {phase.value}/{action.value}: {reasoning[:50]}...")

        return trace

    def record_query_expansion(
        self,
        original_query: str,
        expanded_queries: list[str],
        reasoning: str,
        confidence: float = 0.85
    ) -> ReasoningTrace:
        """记录查询扩展决策

        便捷方法，专门用于记录搜索词扩展的决策。
        """
        return self.record_decision(
            phase=ResearchPhase.SEARCHING,
            action=ReasoningAction.EXPAND_QUERY,
            reasoning=reasoning,
            confidence=confidence,
            metadata={
                "original_query": original_query,
                "expanded_queries": expanded_queries
            }
        )

    def record_source_selection(
        self,
        selected_url: str,
        selected_reason: str,
        skipped_sources: list[dict] | None = None,
        confidence: float = 0.8
    ) -> ReasoningTrace:
        """记录来源选择决策

        Args:
            selected_url: 选中的来源 URL
            selected_reason: 选择原因
            skipped_sources: 跳过的来源列表 [{"url": ..., "reason": ...}]
        """
        alternatives = []
        if skipped_sources:
            for src in skipped_sources:
                alternatives.append({
                    "description": src.get("url", ""),
                    "reason_rejected": src.get("reason", "内容不相关")
                })

        return self.record_decision(
            phase=ResearchPhase.READING,
            action=ReasoningAction.SELECT_SOURCE,
            reasoning=selected_reason,
            confidence=confidence,
            alternatives=alternatives,
            evidence=[{
                "source": selected_url,
                "content": "选中作为研究来源",
                "relevance": 0.9
            }]
        )

    def record_contradiction_detection(
        self,
        claim: str,
        conflicting_sources: list[dict],
        confidence: float = 0.7
    ) -> ReasoningTrace:
        """记录矛盾检测决策

        Args:
            claim: 存在矛盾的声明
            conflicting_sources: 冲突的来源列表 [{"source": ..., "value": ...}]
        """
        evidence = []
        for src in conflicting_sources:
            evidence.append({
                "source": src.get("source", ""),
                "content": f"声称: {src.get('value', '')}",
                "relevance": 0.9
            })

        return self.record_decision(
            phase=ResearchPhase.VERIFYING,
            action=ReasoningAction.DETECT_CONTRADICTION,
            reasoning=f"检测到关于「{claim}」的信息存在矛盾，需要进一步验证",
            confidence=confidence,
            evidence=evidence,
            metadata={"claim": claim, "sources_count": len(conflicting_sources)}
        )

    def record_depth_adjustment(
        self,
        new_depth: str,
        reason: str,
        confidence: float = 0.75
    ) -> ReasoningTrace:
        """记录深度调整决策"""
        return self.record_decision(
            phase=ResearchPhase.ANALYZING,
            action=ReasoningAction.ADJUST_DEPTH,
            reasoning=reason,
            confidence=confidence,
            metadata={"new_depth": new_depth}
        )

    def to_sse_event(self, trace: ReasoningTrace) -> SSEEvent:
        """将推理轨迹转换为 SSE 事件"""
        return SSEEvent(
            type=SSEEventType.REASONING_DECISION,
            data={
                "id": trace.id,
                "timestamp": trace.timestamp.isoformat(),
                "phase": trace.phase.value,
                "action": trace.action.value,
                "reasoning": trace.reasoning,
                "confidence": trace.confidence,
                "alternatives": [
                    {"description": alt.description, "reason": alt.reason_rejected}
                    for alt in trace.alternatives
                ],
                "evidence": [
                    {"source": ev.source, "content": ev.content}
                    for ev in trace.evidence
                ],
                "metadata": trace.metadata
            }
        )

    async def stream_decision(
        self,
        phase: ResearchPhase,
        action: ReasoningAction,
        reasoning: str,
        **kwargs
    ) -> AsyncGenerator[SSEEvent, None]:
        """记录决策并立即流式推送

        用于在研究过程中实时向前端推送推理信息。
        """
        trace = self.record_decision(phase, action, reasoning, **kwargs)
        yield self.to_sse_event(trace)

    def add_feedback(self, feedback: ReasoningTraceFeedback) -> bool:
        """添加用户对某条推理的反馈

        用于收集用户反馈以改进 AI 决策。
        """
        if not any(t.id == feedback.trace_id for t in self._traces):
            return False

        self._feedback[feedback.trace_id] = feedback
        logger.info(
            f"[ReasoningTrace] Feedback received: {feedback.trace_id} "
            f"= {feedback.feedback}"
        )
        return True

    def get_all_traces(self) -> list[ReasoningTrace]:
        """获取所有推理轨迹"""
        return self._traces

    def get_recent_traces(self, limit: int = 5) -> list[ReasoningTrace]:
        """获取最近的推理轨迹"""
        return self._traces[-limit:] if self._traces else []

    def get_trace_by_id(self, trace_id: str) -> ReasoningTrace | None:
        """根据 ID 获取推理轨迹"""
        for trace in self._traces:
            if trace.id == trace_id:
                return trace
        return None

    def clear(self):
        """清空所有轨迹 (用于新研究会话)"""
        self._traces = []
        self._feedback = {}


# 全局存储 (生产环境应使用 Redis)
_session_traces: dict[str, ReasoningTraceService] = {}


def get_reasoning_service(session_id: str) -> ReasoningTraceService:
    """获取或创建会话的推理轨迹服务"""
    if session_id not in _session_traces:
        _session_traces[session_id] = ReasoningTraceService(session_id)
    return _session_traces[session_id]


def clear_session_traces(session_id: str):
    """清除会话的推理轨迹"""
    if session_id in _session_traces:
        del _session_traces[session_id]
