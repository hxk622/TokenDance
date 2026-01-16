"""
Adaptive Loader - 自适应资源延迟加载

基于当前任务预测接下来需要的 Skill / 文档 / 工具，提前加载以减少等待。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional, Set
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class PredictedResource:
    """预测需要加载的资源"""
    resource_type: str  # "skill" | "document" | "tool"
    resource_id: str
    confidence: float  # 预测置信度 (0-1)


class AdaptiveLoader:
    """
    自适应延迟加载器

    根据对话历史和当前执行状态，预测接下来可能需要的资源并提前加载。
    """

    def __init__(self):
        # 简单的关键词 → 资源映射表（实际项目可用向量检索）
        self._keyword_resource_map: Dict[str, List[PredictedResource]] = {
            # 数据处理关键词
            "csv": [
                PredictedResource("skill", "data_analysis", 0.9),
                PredictedResource("document", "pandas_guide", 0.7),
            ],
            "json": [
                PredictedResource("skill", "json_parser", 0.85),
            ],
            "数据": [
                PredictedResource("skill", "data_analysis", 0.8),
            ],
            # 代码相关
            "代码": [
                PredictedResource("tool", "code_sandbox", 0.9),
            ],
            "python": [
                PredictedResource("tool", "code_sandbox", 0.95),
                PredictedResource("document", "python_stdlib", 0.6),
            ],
            # 研究相关
            "研究": [
                PredictedResource("skill", "deep_research", 0.9),
            ],
            "调研": [
                PredictedResource("skill", "deep_research", 0.85),
            ],
            "报告": [
                PredictedResource("skill", "report_generation", 0.8),
            ],
            # 文件操作
            "文件": [
                PredictedResource("tool", "file_system", 0.9),
            ],
            "读取": [
                PredictedResource("tool", "file_system", 0.8),
            ],
            "写入": [
                PredictedResource("tool", "file_system", 0.85),
            ],
        }

        # 已加载的资源缓存
        self._loaded: Set[str] = set()

    def predict_next_resources(
        self,
        conversation_history: List[str],
        current_state: str,
        max_predictions: int = 5,
    ) -> List[PredictedResource]:
        """
        预测接下来需要的资源

        Args:
            conversation_history: 最近 N 条对话（用户 + 助手）
            current_state: 当前 Agent 状态 (REASONING / TOOL_CALLING 等)
            max_predictions: 最多返回多少条预测

        Returns:
            按置信度降序的预测资源列表
        """
        combined_text = " ".join(conversation_history).lower()
        predictions: Dict[str, PredictedResource] = {}

        for keyword, resources in self._keyword_resource_map.items():
            if keyword.lower() in combined_text:
                for res in resources:
                    key = f"{res.resource_type}:{res.resource_id}"
                    # 若已存在，取较高置信度
                    if key not in predictions or predictions[key].confidence < res.confidence:
                        predictions[key] = res

        # 按置信度降序
        sorted_preds = sorted(predictions.values(), key=lambda p: p.confidence, reverse=True)
        return sorted_preds[:max_predictions]

    def mark_loaded(self, resource_type: str, resource_id: str) -> None:
        """标记资源已加载"""
        self._loaded.add(f"{resource_type}:{resource_id}")

    def is_loaded(self, resource_type: str, resource_id: str) -> bool:
        """检查资源是否已加载"""
        return f"{resource_type}:{resource_id}" in self._loaded

    def filter_unloaded(
        self, predictions: List[PredictedResource]
    ) -> List[PredictedResource]:
        """过滤掉已加载的资源"""
        return [
            p
            for p in predictions
            if not self.is_loaded(p.resource_type, p.resource_id)
        ]

    def preload_resources(
        self,
        predictions: List[PredictedResource],
        loader_fn: Optional[callable] = None,
    ) -> int:
        """
        预加载资源

        Args:
            predictions: 预测的资源列表
            loader_fn: 实际加载函数 (resource_type, resource_id) -> bool

        Returns:
            成功加载的资源数
        """
        unloaded = self.filter_unloaded(predictions)
        loaded_count = 0
        for pred in unloaded:
            if loader_fn:
                success = loader_fn(pred.resource_type, pred.resource_id)
                if success:
                    self.mark_loaded(pred.resource_type, pred.resource_id)
                    loaded_count += 1
                    logger.info(
                        f"Preloaded {pred.resource_type}:{pred.resource_id} "
                        f"(confidence={pred.confidence:.2f})"
                    )
            else:
                # 无 loader_fn 时仅标记
                self.mark_loaded(pred.resource_type, pred.resource_id)
                loaded_count += 1
        return loaded_count
