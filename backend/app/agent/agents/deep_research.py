# -*- coding: utf-8 -*-
"""
DeepResearchAgent - 深度研究 Agent

实现 Manus 级别的深度研究能力：
- 多轮搜索与查询扩展 (QueryExpansion)
- 来源可信度评估 (SourceCredibility)  
- 信息综合与冲突解决 (InformationSynthesis)
- 结构化报告生成 (带引用)
- 时光长廊 (研究轨迹截图回溯)

设计原则：
- 大模型在"宏观逻辑"上60%成功率，在"微观动作"上99.9%成功率
- 把1个60%成功率的大任务切碎成100个99.9%成功率的小任务
"""
from typing import AsyncGenerator, List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import json
import re
import asyncio

from ..base import BaseAgent
from ..types import SSEEvent, SSEEventType, AgentAction, ActionType

logger = logging.getLogger(__name__)

# 并发配置
MAX_CONCURRENT_TOOLS = 10  # 最大并发工具执行数


# ==================== 数据模型 ====================

class SourceCredibility(Enum):
    """来源可信度等级"""
    AUTHORITATIVE = "authoritative"      # 权威来源 (学术期刊、官方文档)
    RELIABLE = "reliable"                 # 可靠来源 (知名媒体、专业博客)
    MODERATE = "moderate"                 # 一般来源 (普通网站)
    QUESTIONABLE = "questionable"         # 可疑来源 (未知来源)
    UNRELIABLE = "unreliable"            # 不可靠来源 (已知假信息源)


@dataclass
class ResearchSource:
    """研究来源"""
    url: str
    title: str
    snippet: str
    credibility: SourceCredibility = SourceCredibility.MODERATE
    timestamp: datetime = field(default_factory=datetime.now)
    content: Optional[str] = None        # 完整内容 (read_url 后填充)
    screenshot_path: Optional[str] = None  # 截图路径 (时光长廊)
    key_findings: List[str] = field(default_factory=list)
    
    def to_citation(self, index: int) -> str:
        """生成引用格式"""
        date_str = self.timestamp.strftime("%Y-%m-%d")
        return f"[{index}] {self.title}. {self.url}. Accessed: {date_str}"


@dataclass
class ResearchFinding:
    """研究发现"""
    content: str
    sources: List[ResearchSource]
    confidence: float  # 0.0 - 1.0
    conflicting_sources: List[ResearchSource] = field(default_factory=list)


@dataclass
class ResearchState:
    """研究状态 (Working Memory)"""
    topic: str
    queries_executed: List[str] = field(default_factory=list)
    sources_collected: List[ResearchSource] = field(default_factory=list)
    findings: List[ResearchFinding] = field(default_factory=list)
    knowledge_gaps: List[str] = field(default_factory=list)
    phase: str = "init"  # init -> searching -> reading -> synthesizing -> reporting
    iteration: int = 0
    max_sources: int = 10
    min_credible_sources: int = 3


# ==================== 核心 Agent ====================

class DeepResearchAgent(BaseAgent):
    """深度研究 Agent
    
    继承 ResearchAgent，扩展以下能力：
    - 多轮搜索：基于初始结果扩展查询
    - 来源评估：自动评估来源可信度
    - 信息综合：识别共识与冲突
    - 报告生成：带引用的结构化报告
    
    工作流：
    1. 理解研究主题 → 生成初始查询
    2. 执行搜索 → 收集来源
    3. 评估来源 → 筛选高质量来源
    4. 深度阅读 → 提取关键发现
    5. 扩展查询 → 填补知识空白
    6. 信息综合 → 生成报告
    """
    
    def __init__(self, *args, max_concurrent: int = MAX_CONCURRENT_TOOLS, **kwargs):
        super().__init__(*args, **kwargs)
        self.research_state: Optional[ResearchState] = None
        self._action_count = 0  # 用于 2-Action Rule
        self._max_concurrent = max_concurrent  # 最大并发数
        self._semaphore = asyncio.Semaphore(max_concurrent)  # 并发控制
        self._pending_urls: List[str] = []  # 待并发读取的 URL
        self._pending_queries: List[str] = []  # 待并发搜索的查询
    
    async def _think(self) -> AsyncGenerator[SSEEvent, None]:
        """思考过程 - DeepResearch 版本
        
        根据当前研究阶段进行针对性思考
        """
        logger.debug("DeepResearchAgent thinking...")
        
        phase = self.research_state.phase if self.research_state else "init"
        
        # 阶段性思考提示
        thinking_prompts = {
            "init": "🎯 Analyzing research topic and planning initial search strategy...",
            "searching": "🔍 Evaluating search results and identifying knowledge gaps...",
            "reading": "📖 Extracting key findings and assessing source credibility...",
            "synthesizing": "🔗 Synthesizing information and resolving conflicts...",
            "reporting": "📝 Generating structured research report..."
        }
        
        yield SSEEvent(
            type=SSEEventType.THINKING,
            data={'content': thinking_prompts.get(phase, "Thinking...") + "\n"}
        )
        
        # 构造思考系统提示
        system_prompt = self._get_thinking_prompt(phase)
        
        # 使用 LLM 进行思考
        thinking_content = ""
        async for chunk in self.llm.stream(
            messages=self.context.messages,
            system=system_prompt
        ):
            thinking_content += chunk
            yield SSEEvent(
                type=SSEEventType.THINKING,
                data={'content': chunk}
            )
        
        # 保存思考内容
        self.context.append_thinking(thinking_content)
        
        # 解析思考结果，更新研究状态
        await self._update_state_from_thinking(thinking_content)
        
        logger.debug(f"Thinking complete, phase: {phase}")
    
    def _get_thinking_prompt(self, phase: str) -> str:
        """获取阶段性思考提示"""
        
        base_prompt = """You are a deep research assistant conducting systematic research.

Current Research State:
"""
        if self.research_state:
            base_prompt += f"""- Topic: {self.research_state.topic}
- Phase: {phase}
- Sources collected: {len(self.research_state.sources_collected)}
- Queries executed: {len(self.research_state.queries_executed)}
- Knowledge gaps: {self.research_state.knowledge_gaps}
"""
        
        phase_prompts = {
            "init": """
Analyze the research topic and:
1. Break down the topic into key aspects to investigate
2. Generate 3-5 specific search queries
3. Identify potential authoritative sources

Output your thinking as structured analysis.""",

            "searching": """
Evaluate the current search results:
1. Assess source credibility (authoritative, reliable, moderate, questionable)
2. Identify knowledge gaps - what aspects are not yet covered?
3. Generate follow-up queries to fill gaps

Focus on finding diverse, high-quality sources.""",

            "reading": """
For each source being read:
1. Extract key findings and claims
2. Note any data, statistics, or quotes
3. Identify conflicting information
4. Rate information completeness

Be thorough but concise.""",

            "synthesizing": """
Synthesize all collected information:
1. Identify consensus across sources
2. Note conflicting viewpoints and their sources
3. Assess overall confidence in findings
4. Structure the main conclusions

Prepare for report generation.""",

            "reporting": """
Plan the research report structure:
1. Executive summary
2. Key findings by aspect
3. Conflicting viewpoints
4. Limitations and gaps
5. References

Ensure all claims have citations."""
        }
        
        return base_prompt + phase_prompts.get(phase, "Analyze the current situation.")
    
    async def _update_state_from_thinking(self, thinking: str) -> None:
        """从思考内容更新研究状态"""
        if not self.research_state:
            return
        
        # 简单的状态转换逻辑（可以用 LLM 解析更复杂的内容）
        if self.research_state.phase == "init":
            # 提取查询建议
            queries = self._extract_queries_from_thinking(thinking)
            if queries:
                self.research_state.knowledge_gaps = queries
        
        elif self.research_state.phase == "searching":
            # 检查是否需要进入下一阶段
            if len(self.research_state.sources_collected) >= self.research_state.min_credible_sources:
                # 有足够来源，可以开始深度阅读
                pass
    
    def _extract_queries_from_thinking(self, thinking: str) -> List[str]:
        """从思考内容提取查询建议"""
        queries = []
        # 简单正则匹配数字列表格式
        pattern = r'(?:^|\n)\s*\d+[\.\)]\s*(.+?)(?=\n\s*\d+[\.\)]|\n\n|$)'
        matches = re.findall(pattern, thinking, re.MULTILINE)
        for match in matches[:5]:  # 最多5个
            query = match.strip().strip('"\'')
            if len(query) > 10 and len(query) < 200:
                queries.append(query)
        return queries
    
    async def _decide(self) -> AgentAction:
        """决策 - DeepResearch 版本
        
        根据研究阶段决定下一步行动
        """
        logger.debug(f"DeepResearchAgent deciding, phase: {self.research_state.phase if self.research_state else 'init'}")
        
        # 初始化研究状态
        if not self.research_state:
            topic = self._extract_topic_from_context()
            self.research_state = ResearchState(topic=topic)
            logger.info(f"Research initialized for topic: {topic}")
        
        # 获取可用工具
        tool_definitions = self.tools.get_llm_tool_definitions()
        
        if not tool_definitions:
            logger.warning("No tools available, generating answer directly")
            return await self._generate_final_report()
        
        # 根据阶段决定系统提示
        system_prompt = self._get_decision_prompt()
        
        # 调用 LLM 进行决策
        response = await self.llm.complete(
            messages=self.context.messages,
            system=system_prompt,
            tools=tool_definitions
        )
        
        # 处理工具调用
        if response.tool_calls:
            tool_call = response.tool_calls[0]
            
            # 更新 action count (2-Action Rule)
            self._action_count += 1
            
            # 每2次重大操作后，触发写入 findings
            if self._action_count >= 2 and tool_call["name"] in ["web_search", "read_url", "browser_open"]:
                self._action_count = 0
                # 记录到 findings.md
                await self._record_findings()
            
            # 更新阶段
            self._update_phase_from_tool(tool_call["name"])
            
            return AgentAction(
                type=ActionType.TOOL_CALL,
                tool_name=tool_call["name"],
                tool_input=tool_call["input"],
                tool_call_id=tool_call["id"]
            )
        
        # 检查是否应该生成报告
        if self._should_generate_report():
            return await self._generate_final_report()
        
        # 默认继续研究
        answer = response.content.strip()
        return AgentAction(
            type=ActionType.ANSWER,
            answer=answer
        )
    
    def _get_decision_prompt(self) -> str:
        """获取决策提示"""
        phase = self.research_state.phase if self.research_state else "init"
        
        base = """You are conducting deep research. Based on the conversation and your analysis:

Available tools:
- web_search: Search for information (use for broad queries)
- read_url: Read full content from a URL (use for deep reading)
- browser_open: Open page with interactive elements (use for dynamic pages)
- browser_screenshot: Capture page screenshot (use for timeline)

Current research state:
"""
        if self.research_state:
            base += f"""- Topic: {self.research_state.topic}
- Phase: {phase}
- Sources: {len(self.research_state.sources_collected)}/{self.research_state.max_sources}
- Queries done: {self.research_state.queries_executed}
"""
        
        phase_instructions = {
            "init": """
You are starting research. Your first action should be:
1. Use web_search with a well-crafted query about the topic
2. Focus on finding authoritative sources first

Do NOT generate a final answer yet - gather information first.""",

            "searching": """
Continue gathering sources:
1. If you have < 3 credible sources, continue searching with refined queries
2. If you found good sources, use read_url to get full content
3. Consider different perspectives on the topic

Prioritize quality over quantity.""",

            "reading": """
You are in deep reading phase:
1. Use read_url to get full content from promising sources
2. Use browser_screenshot to capture important pages for timeline
3. Once you have enough content, move to synthesis

Extract specific facts, quotes, and data.""",

            "synthesizing": """
You have gathered enough information. Now:
1. If any critical gaps remain, do one more targeted search
2. Otherwise, generate a comprehensive research report

Your report should include:
- Executive Summary
- Key Findings (with citations)
- Conflicting Viewpoints
- Limitations
- References""",

            "reporting": """
Generate the final research report now.
Include all citations and organize findings clearly.
Do NOT call any more tools - provide the complete answer."""
        }
        
        return base + phase_instructions.get(phase, "Continue research based on current needs.")
    
    def _update_phase_from_tool(self, tool_name: str) -> None:
        """根据工具调用更新阶段"""
        if not self.research_state:
            return
        
        if tool_name == "web_search":
            if self.research_state.phase == "init":
                self.research_state.phase = "searching"
        
        elif tool_name in ["read_url", "browser_open"]:
            if self.research_state.phase in ["init", "searching"]:
                self.research_state.phase = "reading"
        
        elif tool_name == "browser_screenshot":
            # 截图不改变阶段
            pass
        
        # 检查是否应该进入综合阶段
        if len(self.research_state.sources_collected) >= self.research_state.min_credible_sources:
            if self.research_state.phase == "reading":
                self.research_state.phase = "synthesizing"
    
    def _should_generate_report(self) -> bool:
        """判断是否应该生成报告"""
        if not self.research_state:
            return False
        
        # 已经在报告阶段
        if self.research_state.phase == "reporting":
            return True
        
        # 达到最大来源数
        if len(self.research_state.sources_collected) >= self.research_state.max_sources:
            self.research_state.phase = "reporting"
            return True
        
        # 迭代次数过多
        if self.research_state.iteration > 15:
            self.research_state.phase = "reporting"
            return True
        
        return False
    
    async def _generate_final_report(self) -> AgentAction:
        """生成最终研究报告"""
        logger.info("Generating final research report...")
        
        # 构造报告生成提示
        system_prompt = """Generate a comprehensive research report based on all gathered information.

Structure:
1. **Executive Summary** (2-3 sentences)
2. **Key Findings** (numbered list with source citations [1], [2], etc.)
3. **Analysis** (synthesize the findings)
4. **Conflicting Viewpoints** (if any)
5. **Limitations & Gaps** (what couldn't be determined)
6. **References** (numbered list of all sources)

Use markdown formatting. Be thorough but concise.
Every factual claim MUST have a citation."""

        # 添加来源信息到上下文
        sources_context = self._format_sources_for_report()
        
        messages = self.context.messages.copy()
        messages.append({
            "role": "user",
            "content": f"Based on the research, generate the final report.\n\nCollected Sources:\n{sources_context}"
        })
        
        response = await self.llm.complete(
            messages=messages,
            system=system_prompt
        )
        
        report = response.content.strip()
        
        # 添加引用部分
        if self.research_state and self.research_state.sources_collected:
            report += "\n\n---\n\n## References\n\n"
            for i, source in enumerate(self.research_state.sources_collected, 1):
                report += source.to_citation(i) + "\n"
        
        # 记录到 findings.md
        await self.memory.write_findings(
            "Research Report Generated",
            report[:2000]  # 摘要
        )
        
        self.research_state.phase = "reporting"
        
        return AgentAction(
            type=ActionType.ANSWER,
            answer=report
        )
    
    def _format_sources_for_report(self) -> str:
        """格式化来源信息用于报告生成"""
        if not self.research_state or not self.research_state.sources_collected:
            return "No sources collected yet."
        
        formatted = ""
        for i, source in enumerate(self.research_state.sources_collected, 1):
            formatted += f"\n[{i}] {source.title}\n"
            formatted += f"    URL: {source.url}\n"
            formatted += f"    Credibility: {source.credibility.value}\n"
            if source.key_findings:
                formatted += f"    Key Findings:\n"
                for finding in source.key_findings:
                    formatted += f"      - {finding}\n"
            if source.snippet:
                formatted += f"    Snippet: {source.snippet[:300]}...\n"
        
        return formatted
    
    async def _record_findings(self) -> None:
        """记录发现到 findings.md (2-Action Rule)"""
        if not self.research_state:
            return
        
        summary = f"Research Progress - Phase: {self.research_state.phase}\n"
        summary += f"Sources: {len(self.research_state.sources_collected)}\n"
        summary += f"Queries: {self.research_state.queries_executed[-3:]}\n"  # 最近3个查询
        
        try:
            await self.memory.write_findings(
                f"Research Update ({self.research_state.topic[:50]})",
                summary
            )
        except Exception as e:
            logger.warning(f"Failed to record findings: {e}")
    
    def _extract_topic_from_context(self) -> str:
        """从上下文提取研究主题"""
        if not self.context.messages:
            return "Unknown topic"
        
        # 获取最后一条用户消息
        for msg in reversed(self.context.messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                # 清理内容，提取主要主题
                topic = content.strip()[:200]
                return topic
        
        return "Unknown topic"
    
    # ==================== 来源可信度评估 ====================
    
    def assess_source_credibility(self, url: str, title: str) -> SourceCredibility:
        """评估来源可信度
        
        基于 URL 域名和标题进行初步评估
        """
        url_lower = url.lower()
        
        # 权威来源模式
        authoritative_patterns = [
            ".gov", ".edu", "arxiv.org", "nature.com", "science.org",
            "ieee.org", "acm.org", "springer.com", "wiley.com",
            "nih.gov", "who.int", "un.org"
        ]
        
        # 可靠来源模式
        reliable_patterns = [
            "github.com", "stackoverflow.com", "medium.com",
            "nytimes.com", "bbc.com", "reuters.com", "theguardian.com",
            "techcrunch.com", "wired.com", "arstechnica.com",
            "docs.python.org", "docs.microsoft.com", "developer.mozilla.org"
        ]
        
        # 检查权威来源
        for pattern in authoritative_patterns:
            if pattern in url_lower:
                return SourceCredibility.AUTHORITATIVE
        
        # 检查可靠来源
        for pattern in reliable_patterns:
            if pattern in url_lower:
                return SourceCredibility.RELIABLE
        
        # 默认为一般可信度
        return SourceCredibility.MODERATE
    
    def add_source(self, url: str, title: str, snippet: str) -> ResearchSource:
        """添加研究来源"""
        credibility = self.assess_source_credibility(url, title)
        
        source = ResearchSource(
            url=url,
            title=title,
            snippet=snippet,
            credibility=credibility
        )
        
        if self.research_state:
            self.research_state.sources_collected.append(source)
            logger.info(f"Added source: {title} (credibility: {credibility.value})")
        
        return source
    
    # ==================== 并发执行支持 ====================
    
    async def _execute_tool_with_semaphore(
        self, 
        tool_name: str, 
        tool_input: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """带信号量控制的工具执行
        
        Args:
            tool_name: 工具名称
            tool_input: 工具输入参数
            
        Returns:
            Tuple[str, Dict]: (工具名, 执行结果)
        """
        async with self._semaphore:
            try:
                tool = self.tools.get(tool_name)
                if not tool:
                    return (tool_name, {"success": False, "error": f"Tool {tool_name} not found"})
                
                result = await tool.execute(**tool_input)
                return (tool_name, result)
            except Exception as e:
                logger.error(f"Tool {tool_name} execution failed: {e}")
                return (tool_name, {"success": False, "error": str(e)})
    
    async def execute_tools_concurrently(
        self,
        tool_calls: List[Tuple[str, Dict[str, Any]]]
    ) -> AsyncGenerator[SSEEvent, None]:
        """并发执行多个工具
        
        Args:
            tool_calls: List of (tool_name, tool_input) tuples
            
        Yields:
            SSEEvent: 执行进度和结果事件
        """
        if not tool_calls:
            return
        
        # 限制并发数
        batch_size = min(len(tool_calls), self._max_concurrent)
        
        yield SSEEvent(
            type=SSEEventType.STATUS,
            data={
                'content': f'🚀 Executing {len(tool_calls)} tools concurrently (max {batch_size} parallel)...\n'
            }
        )
        
        # 创建任务
        tasks = [
            self._execute_tool_with_semaphore(name, inputs)
            for name, inputs in tool_calls
        ]
        
        # 并发执行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        successful = 0
        failed = 0
        
        for i, result in enumerate(results):
            tool_name, tool_input = tool_calls[i]
            
            if isinstance(result, Exception):
                failed += 1
                yield SSEEvent(
                    type=SSEEventType.TOOL_ERROR,
                    data={
                        'tool': tool_name,
                        'error': str(result)
                    }
                )
            else:
                name, output = result
                if output.get("success", False):
                    successful += 1
                    # 处理搜索结果 - 收集 URL
                    if name == "web_search" and output.get("results"):
                        for item in output.get("results", []):
                            url = item.get("link") or item.get("url")
                            if url:
                                self._pending_urls.append(url)
                    
                    # 处理 read_url 结果 - 添加来源
                    if name == "read_url" and output.get("content"):
                        self.add_source(
                            url=output.get("url", ""),
                            title=output.get("title", "Unknown"),
                            snippet=output.get("content", "")[:500]
                        )
                else:
                    failed += 1
                
                yield SSEEvent(
                    type=SSEEventType.TOOL_RESULT,
                    data={
                        'tool': name,
                        'result': output,
                        'success': output.get("success", False)
                    }
                )
        
        yield SSEEvent(
            type=SSEEventType.STATUS,
            data={
                'content': f'✅ Concurrent execution complete: {successful} succeeded, {failed} failed\n'
            }
        )
        
        # 更新 action count
        self._action_count += len(tool_calls)
        
        # 2-Action Rule: 每 2 次重大操作后写入 findings
        if self._action_count >= 2:
            self._action_count = 0
            await self._record_findings()
    
    async def batch_search(self, queries: List[str]) -> AsyncGenerator[SSEEvent, None]:
        """批量并发搜索
        
        Args:
            queries: 搜索查询列表
            
        Yields:
            SSEEvent: 执行事件
        """
        tool_calls = [
            ("web_search", {"query": q, "max_results": 5})
            for q in queries[:self._max_concurrent]  # 限制数量
        ]
        
        if self.research_state:
            self.research_state.queries_executed.extend(queries[:self._max_concurrent])
        
        async for event in self.execute_tools_concurrently(tool_calls):
            yield event
    
    async def batch_read_urls(self, urls: List[str]) -> AsyncGenerator[SSEEvent, None]:
        """批量并发读取 URL
        
        Args:
            urls: URL 列表
            
        Yields:
            SSEEvent: 执行事件
        """
        # 去重并限制数量
        unique_urls = list(dict.fromkeys(urls))[:self._max_concurrent]
        
        tool_calls = [
            ("read_url", {"url": url, "use_jina": True, "max_length": 8000})
            for url in unique_urls
        ]
        
        async for event in self.execute_tools_concurrently(tool_calls):
            yield event
    
    def get_pending_urls(self) -> List[str]:
        """获取待读取的 URL 并清空"""
        urls = self._pending_urls.copy()
        self._pending_urls.clear()
        return urls
    
    def queue_urls_for_reading(self, urls: List[str]) -> None:
        """将 URL 加入待读取队列"""
        self._pending_urls.extend(urls)
    
    # ==================== 流式返回 (Streaming) ====================
    
    async def execute_tools_streaming(
        self,
        tool_calls: List[Tuple[str, Dict[str, Any]]]
    ) -> AsyncGenerator[SSEEvent, None]:
        """流式执行工具 - 使用 asyncio.as_completed 实时返回
        
        与 execute_tools_concurrently 的区别:
        - as_completed: 哪个先完成就先返回，用户更快看到结果
        - gather: 等所有完成后一起返回
        
        Args:
            tool_calls: List of (tool_name, tool_input) tuples
            
        Yields:
            SSEEvent: 实时执行结果
        """
        if not tool_calls:
            return
        
        yield SSEEvent(
            type=SSEEventType.STATUS,
            data={
                'content': f'🚀 Streaming {len(tool_calls)} tools (results as they complete)...\n'
            }
        )
        
        # 创建带索引的任务
        async def execute_with_index(idx: int, name: str, inputs: Dict) -> Tuple[int, str, Dict]:
            result = await self._execute_tool_with_semaphore(name, inputs)
            return (idx, result[0], result[1])
        
        tasks = [
            asyncio.create_task(execute_with_index(i, name, inputs))
            for i, (name, inputs) in enumerate(tool_calls)
        ]
        
        completed = 0
        successful = 0
        failed = 0
        
        # 使用 as_completed 实现流式返回
        for coro in asyncio.as_completed(tasks):
            try:
                idx, tool_name, result = await coro
                completed += 1
                
                if isinstance(result, dict) and result.get("success", False):
                    successful += 1
                    
                    # 处理搜索结果
                    if tool_name == "web_search" and result.get("results"):
                        for item in result.get("results", []):
                            url = item.get("link") or item.get("url")
                            if url:
                                self._pending_urls.append(url)
                    
                    # 处理 read_url 结果
                    if tool_name == "read_url" and result.get("content"):
                        self.add_source(
                            url=result.get("url", ""),
                            title=result.get("title", "Unknown"),
                            snippet=result.get("content", "")[:500]
                        )
                else:
                    failed += 1
                
                # 实时推送结果
                yield SSEEvent(
                    type=SSEEventType.TOOL_RESULT,
                    data={
                        'tool': tool_name,
                        'result': result,
                        'success': result.get("success", False) if isinstance(result, dict) else False,
                        'progress': f"{completed}/{len(tool_calls)}"
                    }
                )
                
            except Exception as e:
                completed += 1
                failed += 1
                logger.error(f"Streaming task error: {e}")
                yield SSEEvent(
                    type=SSEEventType.TOOL_ERROR,
                    data={'error': str(e), 'progress': f"{completed}/{len(tool_calls)}"}
                )
        
        yield SSEEvent(
            type=SSEEventType.STATUS,
            data={
                'content': f'✅ Streaming complete: {successful} succeeded, {failed} failed\n'
            }
        )
        
        # 更新 action count
        self._action_count += len(tool_calls)
        if self._action_count >= 2:
            self._action_count = 0
            await self._record_findings()
    
    async def batch_search_streaming(
        self,
        queries: List[str]
    ) -> AsyncGenerator[SSEEvent, None]:
        """流式批量搜索 - 结果实时返回
        
        用户体验优化:
        - 首个结果延迟: ~2s (之前需要等所有完成: ~10s)
        """
        tool_calls = [
            ("web_search", {"query": q, "max_results": 5})
            for q in queries[:self._max_concurrent]
        ]
        
        if self.research_state:
            self.research_state.queries_executed.extend(queries[:self._max_concurrent])
        
        async for event in self.execute_tools_streaming(tool_calls):
            yield event
    
    async def batch_read_urls_streaming(
        self,
        urls: List[str],
        query: Optional[str] = None
    ) -> AsyncGenerator[SSEEvent, None]:
        """流式批量读取 URL
        
        Args:
            urls: URL 列表
            query: 研究查询 (用于 extract_relevant)
        """
        unique_urls = list(dict.fromkeys(urls))[:self._max_concurrent]
        
        tool_calls = [
            ("read_url", {
                "url": url,
                "use_jina": True,
                "extract_relevant": bool(query),
                "query": query or "",
                "max_length": 8000
            })
            for url in unique_urls
        ]
        
        async for event in self.execute_tools_streaming(tool_calls):
            yield event


# ==================== 工厂函数 ====================

async def create_deep_research_agent(
    context,
    llm,
    tools,
    memory,
    db,
    max_iterations: int = 30,
    max_sources: int = 10,
    max_concurrent: int = MAX_CONCURRENT_TOOLS
) -> DeepResearchAgent:
    """创建 DeepResearchAgent 实例
    
    Args:
        context: AgentContext
        llm: BaseLLM
        tools: ToolRegistry
        memory: WorkingMemory
        db: AsyncSession
        max_iterations: 最大迭代次数（深度研究需要更多迭代）
        max_sources: 最大来源数
        max_concurrent: 最大并发工具执行数 (默认 10)
        
    Returns:
        DeepResearchAgent: Agent 实例
    """
    agent = DeepResearchAgent(
        context=context,
        llm=llm,
        tools=tools,
        memory=memory,
        db=db,
        max_iterations=max_iterations,
        max_concurrent=max_concurrent
    )
    
    # 初始化研究状态参数
    if agent.research_state:
        agent.research_state.max_sources = max_sources
    
    logger.info(
        f"DeepResearchAgent created with max_iterations={max_iterations}, "
        f"max_sources={max_sources}, max_concurrent={max_concurrent}"
    )
    return agent
