"""
专业化 Research Agents

实现:
- SearcherAgent: 搜索 Agent
- ReaderAgent: 阅读/内容提取 Agent
- AnalystAgent: 分析 Agent
- VerifierAgent: 验证 Agent
- SynthesizerAgent: 综合 Agent
"""

import json
import logging
from typing import Any

from .base import AgentResult, AgentRole, AgentTask, BaseResearchAgent, TaskStatus

logger = logging.getLogger(__name__)


class SearcherAgent(BaseResearchAgent):
    """
    搜索 Agent

    负责:
    - Web 搜索
    - 学术搜索
    - 新闻搜索
    - 查询扩展
    """

    def __init__(
        self,
        llm_client: Any = None,
        model: str = "gpt-4o-mini",
        search_function: Any = None,  # 搜索函数 (如 web_search)
    ):
        super().__init__(
            role=AgentRole.SEARCHER,
            llm_client=llm_client,
            model=model,
        )
        self.search_function = search_function
        self._capabilities = [
            "web_search",
            "query_expansion",
            "search_filtering",
        ]

    def can_handle(self, task: AgentTask) -> bool:
        return task.type == "search"

    async def execute(self, task: AgentTask) -> AgentResult:
        query = task.input_data.get("query", "")
        num_results = task.input_data.get("num_results", 10)
        task.input_data.get("search_type", "web")

        if not query:
            return self._create_result(
                task, TaskStatus.FAILED, {}, error="Missing query"
            )

        try:
            # 1. 查询扩展 (可选)
            if task.input_data.get("expand_query", False) and self.llm_client:
                expanded_queries = await self._expand_query(query)
            else:
                expanded_queries = [query]

            # 2. 执行搜索
            all_results = []
            for q in expanded_queries:
                if self.search_function:
                    results = await self.search_function(q, num_results=num_results)
                    all_results.extend(results)
                else:
                    # 模拟搜索结果
                    all_results.append({
                        "title": f"Search result for: {q}",
                        "url": f"https://example.com/search?q={q}",
                        "snippet": f"This is a placeholder result for query: {q}",
                    })

            # 3. 去重和排序
            seen_urls = set()
            unique_results = []
            for r in all_results:
                url = r.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_results.append(r)

            # 4. 返回结果
            return self._create_result(
                task,
                TaskStatus.COMPLETED,
                {
                    "results": unique_results[:num_results],
                    "queries_used": expanded_queries,
                    "total_found": len(unique_results),
                },
                confidence=0.9 if unique_results else 0.5,
                next_actions=["read"] if unique_results else ["refine_search"],
            )

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return self._create_result(task, TaskStatus.FAILED, {}, error=str(e))

    async def _expand_query(self, query: str) -> list[str]:
        """使用 LLM 扩展查询"""
        prompt = f"""为以下搜索查询生成 2-3 个相关的变体查询，以获得更全面的搜索结果。

原始查询: {query}

以 JSON 数组格式返回查询列表，包含原始查询。
示例: ["原始查询", "变体1", "变体2"]

只返回 JSON 数组。"""

        try:
            response = await self._call_llm(prompt, json_mode=True, temperature=0.3)
            queries = json.loads(response)
            if isinstance(queries, list):
                return queries[:4]  # 最多 4 个查询
        except (json.JSONDecodeError, TypeError, KeyError):
            pass
        except Exception as e:
            logger.debug(f"Query expansion failed: {e}")

        return [query]


class ReaderAgent(BaseResearchAgent):
    """
    阅读 Agent

    负责:
    - URL 内容抓取
    - 内容摘要
    - 实体提取
    - 结构化信息提取
    """

    def __init__(
        self,
        llm_client: Any = None,
        model: str = "gpt-4o-mini",
        fetch_function: Any = None,  # URL 抓取函数
    ):
        super().__init__(
            role=AgentRole.READER,
            llm_client=llm_client,
            model=model,
        )
        self.fetch_function = fetch_function
        self._capabilities = [
            "content_extraction",
            "summarization",
            "entity_extraction",
        ]

    def can_handle(self, task: AgentTask) -> bool:
        return task.type == "read"

    async def execute(self, task: AgentTask) -> AgentResult:
        url = task.input_data.get("url", "")
        extract_type = task.input_data.get("extract_type", "content")

        if not url:
            return self._create_result(
                task, TaskStatus.FAILED, {}, error="Missing URL"
            )

        try:
            # 1. 获取内容
            if self.fetch_function:
                content = await self.fetch_function(url)
            else:
                content = f"Placeholder content for {url}"

            if not content:
                return self._create_result(
                    task, TaskStatus.COMPLETED,
                    {"content": "", "url": url, "error": "No content found"},
                    confidence=0.3,
                )

            # 2. 根据类型处理
            if extract_type == "summary":
                result = await self._summarize(content, task.input_data.get("question"))
            elif extract_type == "entities":
                result = await self._extract_entities(content)
            else:
                result = {"content": content[:10000]}  # 截断过长内容

            result["url"] = url
            result["content_length"] = len(content)

            return self._create_result(
                task,
                TaskStatus.COMPLETED,
                result,
                confidence=0.85,
                next_actions=["analyze"] if content else [],
            )

        except Exception as e:
            logger.error(f"Read failed: {e}")
            return self._create_result(task, TaskStatus.FAILED, {}, error=str(e))

    async def _summarize(self, content: str, question: str | None = None) -> dict[str, Any]:
        """生成摘要"""
        if not self.llm_client:
            return {"summary": content[:500]}

        if question:
            prompt = f"""请根据以下问题，从文本中提取相关信息并总结。

问题: {question}

文本:
{content[:8000]}

请提供:
1. 与问题相关的关键信息
2. 简洁的摘要

以 JSON 格式返回: {{"key_points": [...], "summary": "..."}}"""
        else:
            prompt = f"""请总结以下文本的主要内容。

文本:
{content[:8000]}

以 JSON 格式返回: {{"key_points": [...], "summary": "..."}}"""

        try:
            response = await self._call_llm(prompt, json_mode=True, temperature=0.3)
            return json.loads(response)
        except (json.JSONDecodeError, TypeError) as e:
            logger.debug(f"Summarization JSON parse failed: {e}")
            return {"summary": content[:500]}
        except Exception as e:
            logger.warning(f"Summarization failed: {e}")
            return {"summary": content[:500]}

    async def _extract_entities(self, content: str) -> dict[str, Any]:
        """提取实体"""
        if not self.llm_client:
            return {"entities": []}

        prompt = f"""从以下文本中提取关键实体（人物、组织、概念、产品等）。

文本:
{content[:6000]}

以 JSON 格式返回: {{"entities": [{{"name": "...", "type": "person/org/concept/product", "description": "..."}}]}}"""

        try:
            response = await self._call_llm(prompt, json_mode=True, temperature=0.2)
            return json.loads(response)
        except (json.JSONDecodeError, TypeError) as e:
            logger.debug(f"Entity extraction JSON parse failed: {e}")
            return {"entities": []}
        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")
            return {"entities": []}


class AnalystAgent(BaseResearchAgent):
    """
    分析 Agent

    负责:
    - 内容分析
    - 比较分析
    - 趋势分析
    - 洞察生成
    """

    def __init__(
        self,
        llm_client: Any = None,
        model: str = "gpt-4o-mini",
    ):
        super().__init__(
            role=AgentRole.ANALYST,
            llm_client=llm_client,
            model=model,
        )
        self._capabilities = [
            "content_analysis",
            "comparison_analysis",
            "trend_analysis",
            "insight_generation",
        ]

    def can_handle(self, task: AgentTask) -> bool:
        return task.type == "analyze"

    async def execute(self, task: AgentTask) -> AgentResult:
        content = task.input_data.get("content", "")
        analysis_type = task.input_data.get("analysis_type", "general")
        question = task.input_data.get("question")

        if not content:
            return self._create_result(
                task, TaskStatus.FAILED, {}, error="Missing content"
            )

        try:
            if analysis_type == "comparison":
                result = await self._comparison_analysis(content, task.input_data)
            elif analysis_type == "trend":
                result = await self._trend_analysis(content)
            else:
                result = await self._general_analysis(content, question)

            return self._create_result(
                task,
                TaskStatus.COMPLETED,
                result,
                confidence=0.8,
                next_actions=["verify", "synthesize"],
            )

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return self._create_result(task, TaskStatus.FAILED, {}, error=str(e))

    async def _general_analysis(self, content: str, question: str | None) -> dict[str, Any]:
        """通用分析"""
        if not self.llm_client:
            return {"analysis": "LLM not available", "insights": []}

        if question:
            prompt = f"""分析以下内容，回答给定问题。

问题: {question}

内容:
{content[:8000]}

请提供:
1. 对问题的直接回答
2. 关键发现/洞察
3. 置信度评估 (high/medium/low)

以 JSON 格式返回: {{"answer": "...", "insights": [...], "confidence": "..."}}"""
        else:
            prompt = f"""分析以下内容，提取关键信息和洞察。

内容:
{content[:8000]}

请提供:
1. 主要发现
2. 关键洞察
3. 潜在问题或限制

以 JSON 格式返回: {{"main_findings": [...], "insights": [...], "limitations": [...]}}"""

        try:
            response = await self._call_llm(prompt, json_mode=True, temperature=0.5)
            return json.loads(response)
        except (json.JSONDecodeError, TypeError) as e:
            logger.debug(f"General analysis JSON parse failed: {e}")
            return {"analysis": "Analysis failed", "insights": []}
        except Exception as e:
            logger.warning(f"General analysis failed: {e}")
            return {"analysis": "Analysis failed", "insights": []}

    async def _comparison_analysis(self, content: str, input_data: dict) -> dict[str, Any]:
        """比较分析"""
        if not self.llm_client:
            return {"comparison": "LLM not available"}

        items = input_data.get("items", [])
        criteria = input_data.get("criteria", [])

        prompt = f"""对以下内容进行比较分析。

内容:
{content[:8000]}

{"比较项: " + ", ".join(items) if items else ""}
{"比较维度: " + ", ".join(criteria) if criteria else ""}

请提供:
1. 各项的优缺点
2. 综合比较结果
3. 建议/结论

以 JSON 格式返回: {{"items_analysis": [...], "comparison_table": [...], "conclusion": "..."}}"""

        try:
            response = await self._call_llm(prompt, json_mode=True, temperature=0.5)
            return json.loads(response)
        except (json.JSONDecodeError, TypeError) as e:
            logger.debug(f"Comparison analysis JSON parse failed: {e}")
            return {"comparison": "Comparison failed"}
        except Exception as e:
            logger.warning(f"Comparison analysis failed: {e}")
            return {"comparison": "Comparison failed"}

    async def _trend_analysis(self, content: str) -> dict[str, Any]:
        """趋势分析"""
        if not self.llm_client:
            return {"trends": []}

        prompt = f"""分析以下内容中的趋势和模式。

内容:
{content[:8000]}

请识别:
1. 主要趋势
2. 影响因素
3. 未来预测

以 JSON 格式返回: {{"trends": [...], "factors": [...], "predictions": [...]}}"""

        try:
            response = await self._call_llm(prompt, json_mode=True, temperature=0.5)
            return json.loads(response)
        except (json.JSONDecodeError, TypeError) as e:
            logger.debug(f"Trend analysis JSON parse failed: {e}")
            return {"trends": []}
        except Exception as e:
            logger.warning(f"Trend analysis failed: {e}")
            return {"trends": []}


class VerifierAgent(BaseResearchAgent):
    """
    验证 Agent

    负责:
    - 事实核查
    - 声明验证
    - 交叉验证
    - 可信度评估
    """

    def __init__(
        self,
        llm_client: Any = None,
        model: str = "gpt-4o-mini",
        knowledge_graph: Any = None,  # 知识图谱 (用于交叉验证)
    ):
        super().__init__(
            role=AgentRole.VERIFIER,
            llm_client=llm_client,
            model=model,
        )
        self.knowledge_graph = knowledge_graph
        self._capabilities = [
            "fact_checking",
            "claim_verification",
            "cross_validation",
            "credibility_assessment",
        ]

    def can_handle(self, task: AgentTask) -> bool:
        return task.type == "verify"

    async def execute(self, task: AgentTask) -> AgentResult:
        claim = task.input_data.get("claim", "")
        evidence = task.input_data.get("evidence", [])

        if not claim:
            return self._create_result(
                task, TaskStatus.FAILED, {}, error="Missing claim"
            )

        try:
            # 1. 评估证据
            evidence_assessment = await self._assess_evidence(claim, evidence)

            # 2. 使用知识图谱验证 (如果可用)
            if self.knowledge_graph:
                kg_verification = await self._verify_with_knowledge_graph(claim)
            else:
                kg_verification = None

            # 3. 综合判定
            verdict, confidence = self._make_verdict(evidence_assessment, kg_verification)

            return self._create_result(
                task,
                TaskStatus.COMPLETED,
                {
                    "claim": claim,
                    "verdict": verdict,
                    "confidence": confidence,
                    "evidence_assessment": evidence_assessment,
                    "kg_verification": kg_verification,
                },
                confidence=confidence,
                next_actions=["synthesize"] if verdict == "verified" else ["search_more"],
            )

        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return self._create_result(task, TaskStatus.FAILED, {}, error=str(e))

    async def _assess_evidence(self, claim: str, evidence: list[str]) -> dict[str, Any]:
        """评估证据"""
        if not evidence:
            return {"status": "no_evidence", "supporting": [], "contradicting": []}

        if not self.llm_client:
            return {"status": "unable_to_assess", "supporting": [], "contradicting": []}

        prompt = f"""评估以下证据是否支持给定声明。

声明: {claim}

证据:
{chr(10).join(f"{i+1}. {e[:500]}" for i, e in enumerate(evidence[:5]))}

对每条证据判断:
- supports: 支持声明
- contradicts: 与声明矛盾
- neutral: 无关/中立

以 JSON 格式返回: {{"assessments": [{{"evidence_index": 1, "verdict": "supports/contradicts/neutral", "reason": "..."}}], "overall": "verified/contradicted/uncertain"}}"""

        try:
            response = await self._call_llm(prompt, json_mode=True, temperature=0.2)
            return json.loads(response)
        except:
            return {"status": "assessment_failed", "supporting": [], "contradicting": []}

    async def _verify_with_knowledge_graph(self, claim: str) -> dict[str, Any] | None:
        """使用知识图谱验证"""
        # TODO: 集成 knowledge_graph 模块
        return None

    def _make_verdict(
        self,
        evidence_assessment: dict,
        kg_verification: dict | None
    ) -> tuple:
        """综合判定"""
        overall = evidence_assessment.get("overall", "uncertain")

        if overall == "verified":
            return "verified", 0.85
        elif overall == "contradicted":
            return "contradicted", 0.8
        else:
            return "uncertain", 0.5


class SynthesizerAgent(BaseResearchAgent):
    """
    综合 Agent

    负责:
    - 信息综合
    - 报告生成
    - 结构化输出
    - 引用管理
    """

    def __init__(
        self,
        llm_client: Any = None,
        model: str = "gpt-4o-mini",
    ):
        super().__init__(
            role=AgentRole.SYNTHESIZER,
            llm_client=llm_client,
            model=model,
        )
        self._capabilities = [
            "information_synthesis",
            "report_generation",
            "citation_management",
        ]

    def can_handle(self, task: AgentTask) -> bool:
        return task.type == "synthesize"

    async def execute(self, task: AgentTask) -> AgentResult:
        findings = task.input_data.get("findings", [])
        format_type = task.input_data.get("format_type", "report")
        question = task.input_data.get("question")

        if not findings:
            return self._create_result(
                task, TaskStatus.FAILED, {}, error="No findings to synthesize"
            )

        try:
            if format_type == "report":
                result = await self._generate_report(findings, question)
            elif format_type == "summary":
                result = await self._generate_summary(findings, question)
            elif format_type == "outline":
                result = await self._generate_outline(findings, question)
            else:
                result = await self._generate_report(findings, question)

            return self._create_result(
                task,
                TaskStatus.COMPLETED,
                result,
                confidence=0.9,
            )

        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return self._create_result(task, TaskStatus.FAILED, {}, error=str(e))

    async def _generate_report(self, findings: list[dict], question: str | None) -> dict[str, Any]:
        """生成报告"""
        if not self.llm_client:
            return {"report": "LLM not available"}

        findings_text = "\n\n".join(
            f"发现 {i+1}:\n{json.dumps(f, ensure_ascii=False, indent=2)[:1000]}"
            for i, f in enumerate(findings[:10])
        )

        prompt = f"""基于以下研究发现，生成一份综合报告。

{"研究问题: " + question if question else ""}

研究发现:
{findings_text}

请生成一份结构化报告，包含:
1. 摘要
2. 关键发现
3. 详细分析
4. 结论与建议
5. 参考来源

以 Markdown 格式输出报告。"""

        try:
            response = await self._call_llm(
                prompt,
                system_prompt="你是一个专业的研究报告撰写助手。请生成清晰、专业、有深度的报告。",
                temperature=0.7,
                max_tokens=4000,
            )
            return {
                "report": response,
                "format": "markdown",
                "sources_count": len(findings),
            }
        except:
            return {"report": "Report generation failed"}

    async def _generate_summary(self, findings: list[dict], question: str | None) -> dict[str, Any]:
        """生成摘要"""
        if not self.llm_client:
            return {"summary": "LLM not available"}

        findings_text = "\n".join(
            f"- {json.dumps(f, ensure_ascii=False)[:200]}"
            for f in findings[:10]
        )

        prompt = f"""基于以下研究发现，生成简洁摘要。

{"问题: " + question if question else ""}

发现:
{findings_text}

请用 3-5 句话总结核心内容。"""

        try:
            response = await self._call_llm(prompt, temperature=0.5, max_tokens=500)
            return {"summary": response}
        except:
            return {"summary": "Summary generation failed"}

    async def _generate_outline(self, findings: list[dict], question: str | None) -> dict[str, Any]:
        """生成大纲"""
        if not self.llm_client:
            return {"outline": []}

        findings_text = "\n".join(
            f"- {json.dumps(f, ensure_ascii=False)[:200]}"
            for f in findings[:10]
        )

        prompt = f"""基于以下研究发现，生成报告大纲。

{"主题: " + question if question else ""}

发现:
{findings_text}

以 JSON 格式返回大纲: {{"outline": [{{"title": "...", "subtopics": [...]}}]}}"""

        try:
            response = await self._call_llm(prompt, json_mode=True, temperature=0.5)
            return json.loads(response)
        except:
            return {"outline": []}
