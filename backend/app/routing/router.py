"""
ExecutionRouter - 执行路由决策引擎

负责分析用户意图和任务特征，决定采用哪条执行路径：
- Path A: Skill 执行（高置信度匹配，预制脚本）
- Path B: MCP 代码执行（动态代码生成，结构化任务）
- Path C: LLM 推理（非结构化或临时需求）
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ExecutionPath(Enum):
    """执行路径枚举"""
    SKILL = "skill"           # 高置信度 Skill 执行
    MCP_CODE = "mcp_code"     # 动态代码生成 + 沙箱执行
    LLM_REASONING = "llm"     # 纯 LLM 推理


@dataclass
class RoutingDecision:
    """路由决策结果"""
    path: ExecutionPath
    confidence: float          # 决策置信度 [0.0, 1.0]
    reason: str               # 决策理由（用于调试和日志）
    fallback_path: Optional[ExecutionPath] = None  # 失败时的备选路径


class ExecutionRouter:
    """
    智能执行路由器
    
    根据用户意图、任务特征、Skill 匹配结果等信息，决定采用哪条执行路径。
    """

    # 结构化任务关键词（触发 MCP 代码执行）
    STRUCTURED_KEYWORDS = {
        # 数据查询与筛选
        "query", "select", "filter", "search", "find", "match",
        "extract", "fetch", "retrieve", "get",
        
        # 数据处理与转换
        "transform", "convert", "parse", "format", "process",
        "aggregate", "group", "sort", "rank", "order",
        
        # 计算与统计
        "calculate", "compute", "sum", "count", "average", "mean",
        "median", "std", "variance", "statistics", "analyze",
        
        # 数据文件操作
        "csv", "json", "xml", "yaml", "dataframe", "excel",
        "read", "write", "export", "import", "save",
        
        # 代码相关（用户明确要求代码）
        "code", "script", "program", "execute", "run",
        "implement", "algorithm", "function",
        
        # 数据库相关
        "database", "sql", "query", "table", "record",
        
        # 其他分析相关
        "analysis", "report", "statistics", "trend", "visualization",
        "chart", "graph", "plot"
    }

    # 非结构化任务关键词（倾向 LLM 推理）
    UNSTRUCTURED_KEYWORDS = {
        "think", "consider", "discuss", "explain", "describe",
        "write", "compose", "draft", "summarize", "abstract",
        "brainstorm", "ideate", "plan", "advice", "suggest",
        "what is", "how to", "why", "tell me", "show me"
    }

    def __init__(
        self,
        skill_matcher=None,
        skill_executor=None,
        skill_confidence_threshold: float = 0.85,
        structured_task_confidence: float = 0.70,
    ):
        """
        初始化路由器
        
        Args:
            skill_matcher: SkillMatcher 实例（用于意图匹配）
            skill_executor: SkillExecutor 实例（用于验证 Skill 可执行性）
            skill_confidence_threshold: Skill 匹配置信度阈值 (0-1)
            structured_task_confidence: 结构化任务检测置信度阈值 (0-1)
        """
        self.skill_matcher = skill_matcher
        self.skill_executor = skill_executor
        self.skill_confidence_threshold = skill_confidence_threshold
        self.structured_task_confidence = structured_task_confidence
        
        # 路由决策统计
        self.stats = {
            "total": 0,
            ExecutionPath.SKILL: 0,
            ExecutionPath.MCP_CODE: 0,
            ExecutionPath.LLM_REASONING: 0,
        }
        
        logger.info(
            f"ExecutionRouter initialized: "
            f"skill_threshold={skill_confidence_threshold}, "
            f"structured_threshold={structured_task_confidence}"
        )

    async def route(self, user_message: str) -> RoutingDecision:
        """
        核心路由逻辑：根据用户消息决定执行路径
        
        Args:
            user_message: 用户输入消息
            
        Returns:
            RoutingDecision 对象包含选定的执行路径和决策信息
        """
        self.stats["total"] += 1
        
        # Step 1: 尝试 Skill 匹配
        if self.skill_matcher:
            skill_match = await self.skill_matcher.match(user_message)
            if skill_match and skill_match.score >= self.skill_confidence_threshold:
                # 验证 Skill 是否可执行
                if self._can_execute_skill(skill_match.skill_id):
                    decision = RoutingDecision(
                        path=ExecutionPath.SKILL,
                        confidence=min(skill_match.score, 1.0),
                        reason=f"High-confidence Skill match: {skill_match.skill_id} (score={skill_match.score:.2f})",
                        fallback_path=ExecutionPath.MCP_CODE,
                    )
                    self.stats[ExecutionPath.SKILL] += 1
                    logger.info(f"Route decision: {decision.path.value} - {decision.reason}")
                    return decision
                else:
                    logger.warning(f"Skill {skill_match.skill_id} matched but not executable")
        
        # Step 2: 检查是否是结构化任务
        is_structured, structured_score = self._detect_structured_task(user_message)
        if is_structured and structured_score >= self.structured_task_confidence:
            decision = RoutingDecision(
                path=ExecutionPath.MCP_CODE,
                confidence=structured_score,
                reason=f"Structured task detected (score={structured_score:.2f})",
                fallback_path=ExecutionPath.LLM_REASONING,
            )
            self.stats[ExecutionPath.MCP_CODE] += 1
            logger.info(f"Route decision: {decision.path.value} - {decision.reason}")
            return decision
        
        # Step 3: 降级到 LLM 推理
        decision = RoutingDecision(
            path=ExecutionPath.LLM_REASONING,
            confidence=1.0,
            reason="Unstructured task or no Skill match - fallback to LLM reasoning",
            fallback_path=None,
        )
        self.stats[ExecutionPath.LLM_REASONING] += 1
        logger.info(f"Route decision: {decision.path.value} - {decision.reason}")
        return decision

    def _can_execute_skill(self, skill_id: str) -> bool:
        """
        验证 Skill 是否可执行
        
        Args:
            skill_id: Skill ID
            
        Returns:
            True 表示可执行，False 表示不可执行
        """
        if not self.skill_executor:
            return True  # 如果没有 executor，假设可执行
        
        try:
            # 检查 Skill 是否存在且有可用的 L3 脚本
            return self.skill_executor.can_execute(skill_id)
        except Exception as e:
            logger.warning(f"Error checking Skill executability: {e}")
            return False

    def _detect_structured_task(self, user_message: str) -> Tuple[bool, float]:
        """
        检测任务是否为结构化任务
        
        启发式规则：
        1. 包含结构化任务关键词
        2. 包含数据格式提示（CSV, JSON, DataFrame 等）
        3. 用户明确要求代码执行
        
        Args:
            user_message: 用户消息
            
        Returns:
            (is_structured, confidence) 元组
        """
        message_lower = user_message.lower()
        
        # 关键词频率匹配
        structured_count = sum(
            1 for keyword in self.STRUCTURED_KEYWORDS
            if self._contains_word(message_lower, keyword)
        )
        unstructured_count = sum(
            1 for keyword in self.UNSTRUCTURED_KEYWORDS
            if self._contains_word(message_lower, keyword)
        )
        
        total_relevant = structured_count + unstructured_count
        
        if total_relevant == 0:
            # 无关键词，使用其他启发式
            return self._detect_by_patterns(message_lower)
        
        # 计算结构化任务置信度
        structured_ratio = structured_count / total_relevant if total_relevant > 0 else 0
        return structured_ratio > 0.5, structured_ratio

    def _detect_by_patterns(self, message_lower: str) -> Tuple[bool, float]:
        """
        通过模式匹配检测结构化任务
        
        模式包括：
        - 数据操作（e.g., "在 data.csv 中查找..."）
        - 数学表达式（e.g., "计算 sum([1,2,3])"）
        - 文件操作（e.g., "读取 file.json"）
        """
        # 模式 1: 数据文件提及
        if re.search(r'\.(csv|json|xlsx|xml|yaml|txt|parquet)\b', message_lower):
            return True, 0.8
        
        # 模式 2: 数据结构提及
        data_structure_pattern = r'\b(dataframe|table|list|dict|array|series|record)\b'
        if re.search(data_structure_pattern, message_lower):
            return True, 0.7
        
        # 模式 3: 数学/统计操作
        math_pattern = r'\b(sum|count|average|mean|median|max|min|total|percentage)\s*\('
        if re.search(math_pattern, message_lower):
            return True, 0.8
        
        # 模式 4: SQL/查询相关
        if re.search(r'\b(sql|where|join|group by|order by)\b', message_lower):
            return True, 0.9
        
        # 模式 5: 代码片段提及
        if re.search(r'```|code|script|function|algorithm', message_lower):
            return True, 0.8
        
        # 默认：非结构化
        return False, 0.3

    def _contains_word(self, text: str, word: str) -> bool:
        """
        判断文本中是否包含单词（使用单词边界，防止匹配子串）
        
        Args:
            text: 文本
            word: 单词
            
        Returns:
            True 如果包含，False 否则
        """
        pattern = r'\b' + re.escape(word) + r'\b'
        return re.search(pattern, text) is not None

    def update_threshold(
        self,
        skill_threshold: Optional[float] = None,
        structured_threshold: Optional[float] = None,
    ) -> None:
        """
        动态更新路由阈值（用于 A/B 测试）
        
        Args:
            skill_threshold: 新的 Skill 置信度阈值
            structured_threshold: 新的结构化任务阈值
        """
        if skill_threshold is not None:
            self.skill_confidence_threshold = max(0.0, min(1.0, skill_threshold))
            logger.info(f"Updated skill_confidence_threshold to {self.skill_confidence_threshold}")
        
        if structured_threshold is not None:
            self.structured_task_confidence = max(0.0, min(1.0, structured_threshold))
            logger.info(f"Updated structured_task_confidence to {self.structured_task_confidence}")

    def get_stats(self) -> Dict:
        """
        获取路由决策统计信息
        
        Returns:
            统计字典，包含各路径的调用次数和比例
        """
        total = self.stats["total"]
        if total == 0:
            return self.stats
        
        return {
            **self.stats,
            "skill_ratio": self.stats[ExecutionPath.SKILL] / total,
            "mcp_code_ratio": self.stats[ExecutionPath.MCP_CODE] / total,
            "llm_ratio": self.stats[ExecutionPath.LLM_REASONING] / total,
        }

    def reset_stats(self) -> None:
        """重置统计信息"""
        self.stats = {
            "total": 0,
            ExecutionPath.SKILL: 0,
            ExecutionPath.MCP_CODE: 0,
            ExecutionPath.LLM_REASONING: 0,
        }
        logger.info("Router statistics reset")


# 单例模式：全局路由器实例
_router_instance: Optional[ExecutionRouter] = None


def get_execution_router(
    skill_matcher=None,
    skill_executor=None,
    skill_confidence_threshold: float = 0.85,
    structured_task_confidence: float = 0.75,
) -> ExecutionRouter:
    """
    获取全局 ExecutionRouter 实例（单例）
    
    Args:
        skill_matcher: SkillMatcher 实例
        skill_executor: SkillExecutor 实例
        skill_confidence_threshold: Skill 置信度阈值
        structured_task_confidence: 结构化任务检测阈值
        
    Returns:
        ExecutionRouter 实例
    """
    global _router_instance
    if _router_instance is None:
        _router_instance = ExecutionRouter(
            skill_matcher=skill_matcher,
            skill_executor=skill_executor,
            skill_confidence_threshold=skill_confidence_threshold,
            structured_task_confidence=structured_task_confidence,
        )
    return _router_instance


def reset_execution_router() -> None:
    """重置全局路由器实例（用于测试）"""
    global _router_instance
    _router_instance = None
