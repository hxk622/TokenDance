"""
渐进式摘要服务 (Progressive Summarization)

核心思想:
- 不等所有来源收集完再综合
- 每 N 个来源后立即生成中间摘要
- Context 只保留摘要，原文存文件系统
- 避免 Context 膨胀

Token 优化效果:
- 10 个来源原文: ~30K tokens
- 渐进摘要后: ~5K tokens (节省 80%+)
"""
import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SourceSummary:
    """来源摘要"""
    url: str
    title: str
    key_points: list[str]  # 关键发现 (3-5 条)
    relevance_score: float  # 与查询相关度 0-1
    created_at: datetime = field(default_factory=datetime.now)

    def to_compact(self) -> str:
        """生成紧凑表示 (用于 Context)"""
        points = " | ".join(self.key_points[:3])
        return f"[{self.title}] {points}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "key_points": self.key_points,
            "relevance_score": self.relevance_score,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class IntermediateSynthesis:
    """中间综合"""
    batch_id: int
    sources: list[SourceSummary]
    synthesis: str  # 综合摘要
    consensus_points: list[str]  # 共识点
    conflict_points: list[str]  # 冲突点
    knowledge_gaps: list[str]  # 知识空白
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "sources_count": len(self.sources),
            "synthesis": self.synthesis,
            "consensus_points": self.consensus_points,
            "conflict_points": self.conflict_points,
            "knowledge_gaps": self.knowledge_gaps,
            "created_at": self.created_at.isoformat()
        }


class ProgressiveSummarizer:
    """渐进式摘要器

    工作流程:
    1. 每个来源 -> 提取 3-5 个关键点 (SourceSummary)
    2. 每 N 个来源 -> 生成中间综合 (IntermediateSynthesis)
    3. 最终 -> 合并所有中间综合生成报告

    Context 管理:
    - summaries: 存储所有 SourceSummary
    - syntheses: 存储所有 IntermediateSynthesis
    - 原文存入文件系统
    """

    def __init__(
        self,
        batch_size: int = 3,
        storage_dir: str | None = None,
        llm = None  # BaseLLM instance for summarization
    ):
        """
        Args:
            batch_size: 每多少个来源后生成中间综合
            storage_dir: 原文存储目录
            llm: LLM 实例 (用于摘要生成)
        """
        self.batch_size = batch_size
        self.storage_dir = storage_dir or "/tmp/tokendance/research"
        self.llm = llm

        self.summaries: list[SourceSummary] = []
        self.syntheses: list[IntermediateSynthesis] = []
        self._current_batch: list[SourceSummary] = []
        self._batch_counter = 0

        # 确保存储目录存在
        os.makedirs(self.storage_dir, exist_ok=True)

    async def add_source(
        self,
        url: str,
        title: str,
        content: str,
        query: str
    ) -> SourceSummary:
        """添加来源并提取摘要

        Args:
            url: 来源 URL
            title: 标题
            content: 完整内容
            query: 研究查询

        Returns:
            SourceSummary: 来源摘要
        """
        # 1. 存储原文到文件系统
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        filename = f"{content_hash}_{self._sanitize_filename(title)}.md"
        filepath = os.path.join(self.storage_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\nURL: {url}\n\n---\n\n{content}")

        logger.debug(f"Stored full content at: {filepath}")

        # 2. 提取关键点
        key_points = await self._extract_key_points(content, query)

        # 3. 计算相关度
        relevance_score = self._calculate_relevance(content, query)

        # 4. 创建摘要
        summary = SourceSummary(
            url=url,
            title=title,
            key_points=key_points,
            relevance_score=relevance_score
        )

        self.summaries.append(summary)
        self._current_batch.append(summary)

        logger.info(f"Added source: {title} ({len(key_points)} key points, relevance={relevance_score:.2f})")

        # 5. 检查是否需要生成中间综合
        if len(self._current_batch) >= self.batch_size:
            await self._generate_intermediate_synthesis()

        return summary

    async def _extract_key_points(self, content: str, query: str) -> list[str]:
        """提取关键点

        使用 LLM 或规则提取
        """
        if self.llm:
            # 使用 LLM 提取
            prompt = f"""Extract 3-5 key findings from this content that are relevant to: "{query}"

Content:
{content[:3000]}...

Return as a JSON array of strings. Each finding should be 1-2 sentences.
Example: ["Finding 1...", "Finding 2...", ...]"""

            try:
                response = await self.llm.complete(
                    messages=[{"role": "user", "content": prompt}],
                    system="You are a research assistant. Extract key findings concisely."
                )

                # 尝试解析 JSON
                import re
                json_match = re.search(r'\[.*\]', response.content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())[:5]
            except Exception as e:
                logger.warning(f"LLM extraction failed: {e}")

        # 回退到规则提取
        return self._extract_key_points_rule_based(content, query)

    def _extract_key_points_rule_based(self, content: str, query: str) -> list[str]:
        """基于规则的关键点提取"""
        import re

        key_points = []

        # 提取包含查询关键词的句子
        query_words = set(re.findall(r'\w+', query.lower()))
        sentences = re.split(r'[.!?。！？]', content)

        scored_sentences = []
        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 30 or len(sent) > 300:
                continue

            score = 0
            sent_lower = sent.lower()
            for word in query_words:
                if word in sent_lower:
                    score += 1

            # 包含数字/百分比加分
            if re.search(r'\d+[%$万亿]|\d+\.\d+', sent):
                score += 2

            if score > 0:
                scored_sentences.append((sent, score))

        # 排序并取前 5 句
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        key_points = [s[0] for s in scored_sentences[:5]]

        return key_points if key_points else ["Content analyzed, no specific findings extracted."]

    def _calculate_relevance(self, content: str, query: str) -> float:
        """计算内容与查询的相关度 (0-1)"""
        import re

        content_lower = content.lower()
        query_words = set(re.findall(r'\w+', query.lower()))

        if not query_words:
            return 0.5

        matches = sum(1 for word in query_words if word in content_lower)
        return min(1.0, matches / len(query_words))

    async def _generate_intermediate_synthesis(self) -> IntermediateSynthesis:
        """生成中间综合"""
        self._batch_counter += 1

        logger.info(f"Generating intermediate synthesis for batch {self._batch_counter}")

        # 收集当前批次的关键点
        all_points = []
        for summary in self._current_batch:
            all_points.extend(summary.key_points)

        # 生成综合
        if self.llm:
            synthesis_text = await self._llm_synthesize(all_points)
        else:
            synthesis_text = self._rule_based_synthesize(all_points)

        # 提取共识/冲突/空白
        synthesis = IntermediateSynthesis(
            batch_id=self._batch_counter,
            sources=self._current_batch.copy(),
            synthesis=synthesis_text,
            consensus_points=self._find_consensus(all_points),
            conflict_points=[],  # 需要更复杂的分析
            knowledge_gaps=[]
        )

        self.syntheses.append(synthesis)
        self._current_batch.clear()

        return synthesis

    async def _llm_synthesize(self, points: list[str]) -> str:
        """使用 LLM 综合"""
        prompt = f"""Synthesize these research findings into a coherent summary:

{chr(10).join(f'- {p}' for p in points)}

Write a 2-3 paragraph synthesis that:
1. Identifies the main themes
2. Notes any consensus across sources
3. Highlights important facts and figures"""

        response = await self.llm.complete(
            messages=[{"role": "user", "content": prompt}],
            system="You are a research synthesizer. Be concise and factual."
        )
        return response.content

    def _rule_based_synthesize(self, points: list[str]) -> str:
        """基于规则的综合"""
        return "Key findings from this batch:\n\n" + "\n".join(f"• {p}" for p in points[:10])

    def _find_consensus(self, points: list[str]) -> list[str]:
        """查找共识点 (简单实现: 查找相似表述)"""
        # 简化实现: 返回出现频率高的词汇
        import re
        from collections import Counter

        words = []
        for point in points:
            words.extend(re.findall(r'\w{4,}', point.lower()))

        common = Counter(words).most_common(10)
        return [f"Multiple sources mention: {word}" for word, count in common if count > 1][:3]

    def get_context_summary(self) -> str:
        """获取用于 Context 的紧凑摘要

        这是放入 LLM Context 的内容，而非原文
        """
        parts = []

        # 添加来源摘要
        if self.summaries:
            parts.append("## Sources Analyzed")
            for i, s in enumerate(self.summaries, 1):
                parts.append(f"{i}. {s.to_compact()}")

        # 添加中间综合
        if self.syntheses:
            parts.append("\n## Intermediate Findings")
            for syn in self.syntheses:
                parts.append(f"\n### Batch {syn.batch_id}")
                parts.append(syn.synthesis[:500])
                if syn.consensus_points:
                    parts.append("Consensus: " + "; ".join(syn.consensus_points[:3]))

        return "\n".join(parts)

    def get_token_stats(self) -> dict[str, int]:
        """获取 Token 统计"""
        context_summary = self.get_context_summary()

        # 粗略估算 tokens (4 字符 ≈ 1 token)
        estimated_tokens = len(context_summary) // 4

        return {
            "sources_count": len(self.summaries),
            "syntheses_count": len(self.syntheses),
            "context_chars": len(context_summary),
            "estimated_tokens": estimated_tokens
        }

    def _sanitize_filename(self, name: str) -> str:
        """清理文件名"""
        import re
        return re.sub(r'[^\w\-_]', '_', name)[:50]

    async def finalize(self) -> str:
        """完成研究，生成最终综合

        处理剩余未综合的来源
        """
        # 处理剩余批次
        if self._current_batch:
            await self._generate_intermediate_synthesis()

        # 生成最终报告摘要
        return self.get_context_summary()


# 便捷函数
def create_progressive_summarizer(
    batch_size: int = 3,
    storage_dir: str | None = None,
    llm = None
) -> ProgressiveSummarizer:
    """创建渐进式摘要器"""
    return ProgressiveSummarizer(
        batch_size=batch_size,
        storage_dir=storage_dir,
        llm=llm
    )
