"""
Strategy Adaptation - 策略自适应

根据根因分析结果，动态调整执行策略（路由阈值、工具优先级、验证步骤等）。
"""
from __future__ import annotations

from dataclasses import dataclass

from app.agent.failure.root_cause import RootCause
from app.routing.router import ExecutionRouter


@dataclass
class AdaptationDecision:
    summary: str
    router_updated: bool = False
    notes: str = ""


class StrategyAdaptation:
    """将 RootCause 映射到具体、可执行的引擎/路由调整。"""

    def __init__(self, router: ExecutionRouter | None = None):
        self.router = router

    def apply(self, root: RootCause | None) -> AdaptationDecision:
        if root is None:
            return AdaptationDecision(summary="no root cause")

        updated = False
        notes = []

        # 简单规则：根据类别调整阈值或提示行为
        if self.router:
            if root.category in {"timeout", "rate_limit", "network"}:
                # 降低结构化任务阈值，让更多任务走 MCP/Skill，减少纯 LLM 反复思考
                self.router.update_threshold(structured_threshold=max(0.5, self.router.structured_task_confidence - 0.1))
                updated = True
                notes.append("lowered structured_task_confidence by 0.1")
            elif root.category in {"input_error", "permission"}:
                # 提高 Skill 阈值，避免误匹配；更多请求走 LLM 澄清/确认
                self.router.update_threshold(skill_threshold=min(0.95, self.router.skill_confidence_threshold + 0.05))
                updated = True
                notes.append("raised skill_confidence_threshold by 0.05")

        summary = f"Adapted to {root.category} (conf={root.confidence:.2f}): " + ", ".join(root.strategies[:2])
        return AdaptationDecision(summary=summary, router_updated=updated, notes="; ".join(notes))
