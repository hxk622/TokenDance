"""
Saturation Detector Service - 信息饱和度检测

智能检测研究是否已达到信息饱和，提供自适应深度建议。

核心能力:
- 检测信息重复率
- 分析新信息增量
- 评估研究质量
- 建议继续/停止研究
"""
import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SaturationLevel(str, Enum):
    """饱和度级别"""
    LOW = "low"           # 信息量少，建议继续
    MEDIUM = "medium"     # 中等，可继续也可停止
    HIGH = "high"         # 接近饱和
    SATURATED = "saturated"  # 已饱和，建议停止


class AdviceAction(str, Enum):
    """建议动作"""
    CONTINUE = "continue"      # 继续研究
    CONTINUE_FOCUSED = "continue_focused"  # 聚焦特定方向
    CONSIDER_STOP = "consider_stop"  # 考虑停止
    STOP = "stop"              # 建议停止


@dataclass
class ResearchFinding:
    """研究发现"""
    id: str
    content: str
    source_url: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    key_points: list[str] = field(default_factory=list)
    relevance_score: float = 0.0


@dataclass
class SaturationMetrics:
    """饱和度指标"""
    total_findings: int
    unique_points: int
    duplicate_rate: float  # 重复率 0-1
    new_info_rate: float   # 新信息率 0-1 (最近 N 条中)
    coverage_score: float  # 覆盖度 0-1
    quality_score: float   # 质量分 0-1
    saturation_level: SaturationLevel
    confidence: float      # 置信度 0-1


@dataclass
class DepthAdvice:
    """深度建议"""
    action: AdviceAction
    current_depth: int
    suggested_depth: int | None
    saturation: SaturationMetrics
    reason: str
    focus_suggestions: list[str]  # 建议聚焦的方向
    estimated_new_info: float     # 预估新信息增量


class SaturationDetector:
    """
    信息饱和度检测器

    通过分析研究发现的重复性、新颖性和覆盖度，
    判断研究是否已达到信息饱和点。
    """

    # 配置参数
    MIN_FINDINGS_FOR_DETECTION = 5  # 最少发现数才开始检测
    RECENT_WINDOW = 5               # 最近 N 条用于计算新信息率
    SIMILARITY_THRESHOLD = 0.7      # 相似度阈值
    SATURATION_THRESHOLD = 0.8      # 饱和阈值

    def __init__(self):
        self._findings: list[ResearchFinding] = []
        self._key_point_hashes: set[str] = set()
        self._source_domains: set[str] = set()

    def add_finding(self, finding: ResearchFinding) -> None:
        """添加研究发现"""
        self._findings.append(finding)

        # 提取并记录关键点哈希
        for point in finding.key_points:
            point_hash = self._hash_point(point)
            self._key_point_hashes.add(point_hash)

        # 记录来源域名
        domain = self._extract_domain(finding.source_url)
        if domain:
            self._source_domains.add(domain)

    def detect_saturation(self) -> SaturationMetrics:
        """
        检测信息饱和度

        Returns:
            SaturationMetrics: 饱和度指标
        """
        total = len(self._findings)

        if total < self.MIN_FINDINGS_FOR_DETECTION:
            return SaturationMetrics(
                total_findings=total,
                unique_points=len(self._key_point_hashes),
                duplicate_rate=0.0,
                new_info_rate=1.0,
                coverage_score=total / 10,  # 假设 10 条为完整覆盖
                quality_score=0.5,
                saturation_level=SaturationLevel.LOW,
                confidence=0.3,  # 低置信度
            )

        # 计算重复率
        all_points = []
        for f in self._findings:
            all_points.extend(f.key_points)

        duplicate_rate = self._calculate_duplicate_rate(all_points)

        # 计算最近的新信息率
        new_info_rate = self._calculate_new_info_rate()

        # 计算覆盖度
        coverage_score = self._calculate_coverage()

        # 计算质量分
        quality_score = self._calculate_quality()

        # 综合评估饱和度
        saturation_score = (
            duplicate_rate * 0.3 +
            (1 - new_info_rate) * 0.4 +
            coverage_score * 0.3
        )

        if saturation_score >= 0.85:
            level = SaturationLevel.SATURATED
        elif saturation_score >= 0.7:
            level = SaturationLevel.HIGH
        elif saturation_score >= 0.4:
            level = SaturationLevel.MEDIUM
        else:
            level = SaturationLevel.LOW

        # 置信度基于数据量
        confidence = min(1.0, total / 20)

        return SaturationMetrics(
            total_findings=total,
            unique_points=len(self._key_point_hashes),
            duplicate_rate=duplicate_rate,
            new_info_rate=new_info_rate,
            coverage_score=coverage_score,
            quality_score=quality_score,
            saturation_level=level,
            confidence=confidence,
        )

    def _calculate_duplicate_rate(self, points: list[str]) -> float:
        """计算关键点重复率"""
        if not points:
            return 0.0

        seen = set()
        duplicates = 0

        for point in points:
            point_hash = self._hash_point(point)
            if point_hash in seen:
                duplicates += 1
            seen.add(point_hash)

        return duplicates / len(points)

    def _calculate_new_info_rate(self) -> float:
        """计算最近的新信息率"""
        if len(self._findings) <= self.RECENT_WINDOW:
            return 1.0

        # 获取最近的发现
        recent = self._findings[-self.RECENT_WINDOW:]
        older_hashes = set()

        # 收集较早发现的关键点哈希
        for f in self._findings[:-self.RECENT_WINDOW]:
            for point in f.key_points:
                older_hashes.add(self._hash_point(point))

        # 计算最近发现中的新信息
        new_points = 0
        total_points = 0

        for f in recent:
            for point in f.key_points:
                total_points += 1
                if self._hash_point(point) not in older_hashes:
                    new_points += 1

        return new_points / total_points if total_points > 0 else 0.0

    def _calculate_coverage(self) -> float:
        """计算信息覆盖度"""
        # 基于来源多样性和关键点数量
        source_diversity = min(1.0, len(self._source_domains) / 10)
        point_coverage = min(1.0, len(self._key_point_hashes) / 50)

        return (source_diversity + point_coverage) / 2

    def _calculate_quality(self) -> float:
        """计算研究质量分"""
        if not self._findings:
            return 0.0

        # 基于平均相关度分
        avg_relevance = sum(f.relevance_score for f in self._findings) / len(self._findings)

        # 基于来源质量（暂时简化为来源多样性）
        source_quality = min(1.0, len(self._source_domains) / 5)

        return (avg_relevance + source_quality) / 2

    def _hash_point(self, point: str) -> str:
        """生成关键点的哈希"""
        # 标准化处理
        normalized = point.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        return hashlib.md5(normalized.encode()).hexdigest()[:8]

    def _extract_domain(self, url: str) -> str | None:
        """从 URL 提取域名"""
        try:
            # 简单提取
            if '://' in url:
                url = url.split('://')[1]
            domain = url.split('/')[0]
            return domain.lower()
        except Exception:
            return None

    def reset(self) -> None:
        """重置检测器"""
        self._findings.clear()
        self._key_point_hashes.clear()
        self._source_domains.clear()


class AdaptiveDepthAdvisor:
    """
    自适应深度顾问

    基于饱和度检测结果，提供智能的研究深度建议。
    """

    # 深度配置
    DEPTH_CONFIG = {
        "quick": {"sources": 5, "estimated_time": 2},
        "standard": {"sources": 10, "estimated_time": 5},
        "deep": {"sources": 18, "estimated_time": 10},
        "exhaustive": {"sources": 30, "estimated_time": 20},
    }

    def __init__(self, detector: SaturationDetector):
        self.detector = detector
        self._current_depth = 10  # 默认 standard

    def set_current_depth(self, depth: int) -> None:
        """设置当前研究深度"""
        self._current_depth = depth

    def get_advice(self, query: str = "") -> DepthAdvice:
        """
        获取深度建议

        Args:
            query: 原始查询（用于分析聚焦方向）

        Returns:
            DepthAdvice: 深度建议
        """
        metrics = self.detector.detect_saturation()

        # 根据饱和度级别决定动作
        if metrics.saturation_level == SaturationLevel.SATURATED:
            action = AdviceAction.STOP
            suggested = None
            reason = "信息已饱和，继续研究可能产出重复内容"
            estimated_new = 0.05

        elif metrics.saturation_level == SaturationLevel.HIGH:
            action = AdviceAction.CONSIDER_STOP
            suggested = self._current_depth
            reason = f"信息覆盖度已达 {metrics.coverage_score:.0%}，新增信息量降低"
            estimated_new = 0.15

        elif metrics.saturation_level == SaturationLevel.MEDIUM:
            # 中等饱和度，建议聚焦
            if metrics.new_info_rate < 0.3:
                action = AdviceAction.CONTINUE_FOCUSED
                suggested = self._current_depth + 5
                reason = "整体覆盖良好，建议聚焦特定方向深入"
            else:
                action = AdviceAction.CONTINUE
                suggested = self._current_depth + 5
                reason = "仍有较多新信息可挖掘"
            estimated_new = 0.4

        else:  # LOW
            action = AdviceAction.CONTINUE
            suggested = min(self._current_depth + 10, 30)
            reason = "信息覆盖不足，建议增加研究深度"
            estimated_new = 0.7

        # 生成聚焦建议
        focus_suggestions = self._generate_focus_suggestions(metrics, query)

        return DepthAdvice(
            action=action,
            current_depth=self._current_depth,
            suggested_depth=suggested,
            saturation=metrics,
            reason=reason,
            focus_suggestions=focus_suggestions,
            estimated_new_info=estimated_new,
        )

    def _generate_focus_suggestions(
        self,
        metrics: SaturationMetrics,
        query: str,
    ) -> list[str]:
        """生成聚焦方向建议"""
        suggestions = []

        # 基于覆盖度不足的方面
        if metrics.coverage_score < 0.5:
            suggestions.append("增加更多来源以提高覆盖度")

        if metrics.quality_score < 0.5:
            suggestions.append("寻找更权威的信息来源")

        if len(self.detector._source_domains) < 5:
            suggestions.append("扩展到更多不同的信息源")

        # 如果没有具体建议，给出通用建议
        if not suggestions:
            suggestions = [
                "尝试从不同角度分析问题",
                "寻找相关领域的交叉信息",
                "关注最新的研究或报道",
            ]

        return suggestions[:3]  # 最多 3 条建议

    def should_auto_stop(self, confidence_threshold: float = 0.7) -> bool:
        """
        判断是否应该自动停止研究

        Args:
            confidence_threshold: 置信度阈值

        Returns:
            bool: 是否应该停止
        """
        metrics = self.detector.detect_saturation()

        return (
            metrics.saturation_level == SaturationLevel.SATURATED
            and metrics.confidence >= confidence_threshold
        )


# 工厂函数
def create_saturation_detector() -> SaturationDetector:
    """创建饱和度检测器实例"""
    return SaturationDetector()


def create_depth_advisor(detector: SaturationDetector | None = None) -> AdaptiveDepthAdvisor:
    """创建深度顾问实例"""
    if detector is None:
        detector = SaturationDetector()
    return AdaptiveDepthAdvisor(detector)
