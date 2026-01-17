# -*- coding: utf-8 -*-
"""
Research Orchestrator

实现 Plan → Route → Act → Verify → Stop 循环的研究编排器
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

from .base import (
    BaseResearchAgent, AgentRole, AgentTask, AgentResult,
    TaskStatus, TaskPriority, HandoffMessage, HandoffProtocol, TaskFactory
)
from .agents import (
    SearcherAgent, ReaderAgent, AnalystAgent, VerifierAgent, SynthesizerAgent
)

logger = logging.getLogger(__name__)


class ResearchPhase(Enum):
    """研究阶段"""
    PLAN = "plan"           # 规划阶段
    SEARCH = "search"       # 搜索阶段
    READ = "read"           # 阅读阶段
    ANALYZE = "analyze"     # 分析阶段
    VERIFY = "verify"       # 验证阶段
    SYNTHESIZE = "synthesize"  # 综合阶段
    COMPLETE = "complete"   # 完成


class TerminationReason(Enum):
    """终止原因"""
    SUCCESS = "success"                   # 成功完成
    MAX_ITERATIONS = "max_iterations"     # 达到最大迭代次数
    TIMEOUT = "timeout"                   # 超时
    USER_CANCEL = "user_cancel"           # 用户取消
    ERROR = "error"                       # 错误
    NO_PROGRESS = "no_progress"           # 无进展


@dataclass
class ResearchPlan:
    """研究计划"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    question: str = ""
    sub_questions: List[str] = field(default_factory=list)
    search_queries: List[str] = field(default_factory=list)
    required_sources: int = 5
    verification_required: bool = True
    output_format: str = "report"  # report, summary, outline
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "sub_questions": self.sub_questions,
            "search_queries": self.search_queries,
            "required_sources": self.required_sources,
            "verification_required": self.verification_required,
            "output_format": self.output_format,
        }


@dataclass
class ResearchState:
    """研究状态"""
    phase: ResearchPhase = ResearchPhase.PLAN
    iteration: int = 0
    search_results: List[Dict] = field(default_factory=list)
    read_contents: List[Dict] = field(default_factory=list)
    analysis_results: List[Dict] = field(default_factory=list)
    verification_results: List[Dict] = field(default_factory=list)
    final_report: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    
    # 进度追踪
    urls_visited: Set[str] = field(default_factory=set)
    claims_verified: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "iteration": self.iteration,
            "search_results_count": len(self.search_results),
            "read_contents_count": len(self.read_contents),
            "analysis_results_count": len(self.analysis_results),
            "verification_results_count": len(self.verification_results),
            "has_final_report": self.final_report is not None,
            "errors_count": len(self.errors),
        }


class ResearchOrchestrator:
    """
    研究编排器
    
    协调多个专业化 Agent 完成深度研究任务
    实现 Plan → Route → Act → Verify → Stop 循环
    """
    
    def __init__(
        self,
        llm_client: Any = None,
        model: str = "gpt-4o-mini",
        search_function: Any = None,
        fetch_function: Any = None,
        knowledge_graph: Any = None,
        max_iterations: int = 10,
        timeout: float = 300.0,  # 5 分钟
    ):
        """
        初始化编排器
        
        Args:
            llm_client: LLM 客户端
            model: 使用的模型
            search_function: 搜索函数
            fetch_function: URL 抓取函数
            knowledge_graph: 知识图谱 (用于验证)
            max_iterations: 最大迭代次数
            timeout: 超时时间 (秒)
        """
        self.llm_client = llm_client
        self.model = model
        self.max_iterations = max_iterations
        self.timeout = timeout
        
        # 初始化专业化 Agents
        self.agents: Dict[AgentRole, BaseResearchAgent] = {
            AgentRole.SEARCHER: SearcherAgent(llm_client, model, search_function),
            AgentRole.READER: ReaderAgent(llm_client, model, fetch_function),
            AgentRole.ANALYST: AnalystAgent(llm_client, model),
            AgentRole.VERIFIER: VerifierAgent(llm_client, model, knowledge_graph),
            AgentRole.SYNTHESIZER: SynthesizerAgent(llm_client, model),
        }
        
        # 状态
        self.plan: Optional[ResearchPlan] = None
        self.state = ResearchState()
        self._is_running = False
        self._should_stop = False
        
        # 回调
        self._progress_callback: Optional[callable] = None
    
    def set_progress_callback(self, callback: callable) -> None:
        """设置进度回调函数"""
        self._progress_callback = callback
    
    async def research(
        self,
        question: str,
        output_format: str = "report",
        verification_required: bool = True,
        max_sources: int = 10,
    ) -> Dict[str, Any]:
        """
        执行研究任务
        
        Args:
            question: 研究问题
            output_format: 输出格式 (report, summary, outline)
            verification_required: 是否需要验证
            max_sources: 最大来源数量
            
        Returns:
            研究结果
        """
        self._is_running = True
        self._should_stop = False
        self.state = ResearchState()
        start_time = datetime.now()
        
        try:
            # Phase 1: PLAN - 规划
            await self._notify_progress("开始规划研究...")
            self.plan = await self._create_plan(question, output_format, verification_required, max_sources)
            self.state.phase = ResearchPhase.SEARCH
            
            # Phase 2-5: 迭代执行 Route → Act → Verify
            while not self._should_terminate():
                self.state.iteration += 1
                
                # Route: 确定下一步动作
                next_phase = await self._route()
                
                if next_phase == ResearchPhase.COMPLETE:
                    break
                
                # Act: 执行动作
                await self._act(next_phase)
                
                # 检查超时
                if (datetime.now() - start_time).total_seconds() > self.timeout:
                    return self._create_result(TerminationReason.TIMEOUT)
            
            # Phase 6: SYNTHESIZE - 综合
            if not self._should_stop:
                await self._notify_progress("综合研究结果...")
                await self._synthesize()
            
            return self._create_result(TerminationReason.SUCCESS)
            
        except Exception as e:
            logger.error(f"Research failed: {e}")
            self.state.errors.append(str(e))
            return self._create_result(TerminationReason.ERROR, error=str(e))
            
        finally:
            self._is_running = False
    
    def stop(self) -> None:
        """停止研究"""
        self._should_stop = True
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            "is_running": self._is_running,
            "plan": self.plan.to_dict() if self.plan else None,
            "state": self.state.to_dict(),
            "agents": {
                role.value: agent.get_status()
                for role, agent in self.agents.items()
            },
        }
    
    # ==================== 核心循环方法 ====================
    
    async def _create_plan(
        self,
        question: str,
        output_format: str,
        verification_required: bool,
        max_sources: int
    ) -> ResearchPlan:
        """创建研究计划"""
        plan = ResearchPlan(
            question=question,
            output_format=output_format,
            verification_required=verification_required,
            required_sources=max_sources,
        )
        
        # 使用 LLM 分解问题和生成搜索查询
        if self.llm_client:
            import json
            
            prompt = f"""为以下研究问题创建研究计划。

问题: {question}

请提供:
1. 2-4 个子问题 (分解主问题)
2. 3-5 个搜索查询 (用于 Web 搜索)

以 JSON 格式返回:
{{
  "sub_questions": ["问题1", "问题2", ...],
  "search_queries": ["查询1", "查询2", ...]
}}"""
            
            try:
                response = await self.llm_client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5,
                    response_format={"type": "json_object"},
                )
                data = json.loads(response.choices[0].message.content)
                plan.sub_questions = data.get("sub_questions", [])
                plan.search_queries = data.get("search_queries", [question])
            except:
                plan.search_queries = [question]
        else:
            plan.search_queries = [question]
        
        return plan
    
    async def _route(self) -> ResearchPhase:
        """
        路由决策: 确定下一个阶段
        
        基于当前状态和研究进度决定
        """
        # 如果搜索结果不足，继续搜索
        if len(self.state.search_results) < self.plan.required_sources:
            if self.state.phase in [ResearchPhase.PLAN, ResearchPhase.SEARCH]:
                return ResearchPhase.SEARCH
        
        # 如果有未读取的搜索结果，进行读取
        urls_to_read = [
            r.get("url") for r in self.state.search_results
            if r.get("url") and r.get("url") not in self.state.urls_visited
        ]
        if urls_to_read and len(self.state.read_contents) < self.plan.required_sources:
            return ResearchPhase.READ
        
        # 如果有内容未分析，进行分析
        if self.state.read_contents and len(self.state.analysis_results) < len(self.state.read_contents):
            return ResearchPhase.ANALYZE
        
        # 如果需要验证且有分析结果，进行验证
        if self.plan.verification_required and self.state.analysis_results:
            if len(self.state.verification_results) < len(self.state.analysis_results):
                return ResearchPhase.VERIFY
        
        # 如果有足够的分析结果，可以综合
        if self.state.analysis_results:
            return ResearchPhase.SYNTHESIZE
        
        # 默认继续搜索
        return ResearchPhase.SEARCH if self.state.iteration < 3 else ResearchPhase.COMPLETE
    
    async def _act(self, phase: ResearchPhase) -> None:
        """执行特定阶段的动作"""
        self.state.phase = phase
        
        if phase == ResearchPhase.SEARCH:
            await self._do_search()
        elif phase == ResearchPhase.READ:
            await self._do_read()
        elif phase == ResearchPhase.ANALYZE:
            await self._do_analyze()
        elif phase == ResearchPhase.VERIFY:
            await self._do_verify()
        elif phase == ResearchPhase.SYNTHESIZE:
            await self._synthesize()
    
    async def _do_search(self) -> None:
        """执行搜索"""
        searcher = self.agents[AgentRole.SEARCHER]
        
        # 确定要搜索的查询
        queries_to_search = self.plan.search_queries[:3]  # 最多 3 个查询
        
        await self._notify_progress(f"搜索中... ({len(queries_to_search)} 个查询)")
        
        for query in queries_to_search:
            task = TaskFactory.create_search_task(
                query=query,
                num_results=5,
                expand_query=True,
            )
            
            result = await searcher.run(task)
            
            if result.is_success:
                results = result.output_data.get("results", [])
                self.state.search_results.extend(results)
                logger.info(f"Search found {len(results)} results for: {query}")
    
    async def _do_read(self) -> None:
        """执行阅读"""
        reader = self.agents[AgentRole.READER]
        
        # 获取未访问的 URL
        urls_to_read = [
            r.get("url") for r in self.state.search_results
            if r.get("url") and r.get("url") not in self.state.urls_visited
        ][:5]  # 最多 5 个
        
        await self._notify_progress(f"阅读内容... ({len(urls_to_read)} 个来源)")
        
        # 并行读取
        tasks = []
        for url in urls_to_read:
            task = TaskFactory.create_read_task(
                url=url,
                extract_type="summary",
                question=self.plan.question,
            )
            tasks.append(reader.run(task))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            url = urls_to_read[i]
            self.state.urls_visited.add(url)
            
            if isinstance(result, AgentResult) and result.is_success:
                self.state.read_contents.append({
                    "url": url,
                    **result.output_data,
                })
                logger.info(f"Read content from: {url}")
            elif isinstance(result, Exception):
                logger.error(f"Read failed for {url}: {result}")
    
    async def _do_analyze(self) -> None:
        """执行分析"""
        analyst = self.agents[AgentRole.ANALYST]
        
        # 获取未分析的内容
        contents_to_analyze = self.state.read_contents[len(self.state.analysis_results):]
        
        await self._notify_progress(f"分析内容... ({len(contents_to_analyze)} 个)")
        
        for content in contents_to_analyze[:3]:  # 最多分析 3 个
            content_text = content.get("content", "") or content.get("summary", "")
            if not content_text:
                continue
            
            task = TaskFactory.create_analyze_task(
                content=content_text,
                analysis_type="general",
                question=self.plan.question,
            )
            
            result = await analyst.run(task)
            
            if result.is_success:
                self.state.analysis_results.append({
                    "source_url": content.get("url"),
                    **result.output_data,
                })
    
    async def _do_verify(self) -> None:
        """执行验证"""
        verifier = self.agents[AgentRole.VERIFIER]
        
        await self._notify_progress("验证信息...")
        
        # 收集需要验证的声明
        claims_to_verify = []
        for analysis in self.state.analysis_results:
            # 从分析结果中提取声明
            insights = analysis.get("insights", [])
            for insight in insights[:2]:  # 每个分析最多 2 个
                if isinstance(insight, str) and insight not in self.state.claims_verified:
                    claims_to_verify.append({
                        "claim": insight,
                        "source": analysis.get("source_url"),
                    })
        
        for claim_data in claims_to_verify[:3]:  # 最多验证 3 个
            task = TaskFactory.create_verify_task(
                claim=claim_data["claim"],
                evidence=[c.get("content", "") for c in self.state.read_contents[:3]],
            )
            
            result = await verifier.run(task)
            
            self.state.claims_verified.add(claim_data["claim"])
            
            if result.is_success:
                self.state.verification_results.append({
                    "claim": claim_data["claim"],
                    "source": claim_data["source"],
                    **result.output_data,
                })
    
    async def _synthesize(self) -> None:
        """综合研究结果"""
        synthesizer = self.agents[AgentRole.SYNTHESIZER]
        
        await self._notify_progress("生成研究报告...")
        
        # 收集所有发现
        findings = []
        
        for analysis in self.state.analysis_results:
            findings.append({
                "type": "analysis",
                "source": analysis.get("source_url"),
                "insights": analysis.get("insights", []),
                "answer": analysis.get("answer"),
            })
        
        for verification in self.state.verification_results:
            findings.append({
                "type": "verification",
                "claim": verification.get("claim"),
                "verdict": verification.get("verdict"),
                "confidence": verification.get("confidence"),
            })
        
        task = TaskFactory.create_synthesize_task(
            findings=findings,
            format_type=self.plan.output_format,
            question=self.plan.question,
        )
        
        result = await synthesizer.run(task)
        
        if result.is_success:
            self.state.final_report = result.output_data.get("report") or result.output_data.get("summary")
            self.state.phase = ResearchPhase.COMPLETE
    
    # ==================== 辅助方法 ====================
    
    def _should_terminate(self) -> bool:
        """判断是否应该终止"""
        if self._should_stop:
            return True
        
        if self.state.iteration >= self.max_iterations:
            return True
        
        if self.state.phase == ResearchPhase.COMPLETE:
            return True
        
        return False
    
    def _create_result(
        self,
        reason: TerminationReason,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建最终结果"""
        return {
            "success": reason == TerminationReason.SUCCESS,
            "termination_reason": reason.value,
            "question": self.plan.question if self.plan else "",
            "report": self.state.final_report,
            "statistics": {
                "iterations": self.state.iteration,
                "sources_searched": len(self.state.search_results),
                "sources_read": len(self.state.read_contents),
                "analyses_completed": len(self.state.analysis_results),
                "claims_verified": len(self.state.verification_results),
            },
            "sources": [
                {"url": c.get("url"), "title": c.get("title", "")}
                for c in self.state.read_contents
            ],
            "errors": self.state.errors + ([error] if error else []),
        }
    
    async def _notify_progress(self, message: str) -> None:
        """通知进度"""
        logger.info(f"[{self.state.phase.value}] {message}")
        
        if self._progress_callback:
            try:
                await self._progress_callback({
                    "phase": self.state.phase.value,
                    "iteration": self.state.iteration,
                    "message": message,
                })
            except:
                pass
