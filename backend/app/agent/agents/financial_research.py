# -*- coding: utf-8 -*-
"""
FinancialResearchAgent - 金融投研专属 Agent

继承 DeepResearchAgent，针对金融场景优化：
- 六阶段工作流: scoping → collecting → analyzing → valuating → sentiment → reporting
- 集成金融数据工具 (OpenBB, AkShare)
- 财务分析 + 估值分析 + 市场情绪
- 合规检查与免责声明

核心定位: "和 AI 一起研究"的协作工作台，而非"等 AI 报告"的自动化工具

设计原则:
- 透明 + 可干预: 实时推理可视化，用户可中途调整方向
- Vibe Workflow: 氛围感体验，而非冰冷的数据堆砌
- 合规优先: 只做信息整合，不做投资建议
"""
from typing import AsyncGenerator, List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import re

from .deep_research import DeepResearchAgent, ResearchState, ResearchSource, SourceCredibility
from ..base import BaseAgent
from ..types import SSEEvent, SSEEventType, AgentAction, ActionType

logger = logging.getLogger(__name__)


# ==================== 金融专属数据模型 ====================

class FinancialResearchPhase(str, Enum):
    """金融研究阶段"""
    SCOPING = "scoping"           # 范围界定（个股/行业/宏观）
    COLLECTING = "collecting"     # 数据采集（多源并行）
    ANALYZING = "analyzing"       # 财务分析（指标计算 + 对比）
    VALUATING = "valuating"       # 估值分析（PE/PB/DCF）
    SENTIMENT = "sentiment"       # 市场情绪（舆情 + 资金流）
    REPORTING = "reporting"       # 报告生成（结构化输出）


class ResearchScope(str, Enum):
    """研究范围类型"""
    INDIVIDUAL_STOCK = "individual_stock"  # 个股研究
    INDUSTRY = "industry"                   # 行业研究
    MACRO = "macro"                         # 宏观研究
    THEMATIC = "thematic"                   # 主题研究


class Market(str, Enum):
    """市场类型"""
    US = "us"          # 美股
    CN = "cn"          # A股
    HK = "hk"          # 港股
    GLOBAL = "global"  # 全球


@dataclass
class FinancialData:
    """金融数据"""
    data_type: str  # quote, fundamental, valuation, sentiment, news
    source: str     # openbb, akshare, browser
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 0.8  # 数据可信度


@dataclass
class FinancialMetrics:
    """财务指标"""
    # 盈利能力
    roe: Optional[float] = None          # 净资产收益率
    roa: Optional[float] = None          # 总资产收益率
    gross_margin: Optional[float] = None # 毛利率
    net_margin: Optional[float] = None   # 净利率
    
    # 成长能力
    revenue_growth: Optional[float] = None  # 营收增速
    profit_growth: Optional[float] = None   # 利润增速
    
    # 偿债能力
    debt_ratio: Optional[float] = None      # 资产负债率
    current_ratio: Optional[float] = None   # 流动比率
    
    # 估值指标
    pe_ttm: Optional[float] = None          # 市盈率
    pb: Optional[float] = None              # 市净率
    ps: Optional[float] = None              # 市销率
    
    # 市场数据
    market_cap: Optional[float] = None      # 总市值
    price: Optional[float] = None           # 当前价格
    change_percent: Optional[float] = None  # 涨跌幅


@dataclass
class SentimentData:
    """情绪数据"""
    score: float           # 情绪得分 0-100
    bullish_count: int     # 看多数量
    bearish_count: int     # 看空数量
    neutral_count: int     # 中性数量
    key_topics: List[str]  # 关键话题
    sources: List[str]     # 数据来源


@dataclass
class FinancialResearchState(ResearchState):
    """金融研究状态 (扩展 ResearchState)"""
    # 金融专属字段
    scope: ResearchScope = ResearchScope.INDIVIDUAL_STOCK
    market: Market = Market.US
    symbol: Optional[str] = None
    company_name: Optional[str] = None
    
    # 阶段状态（覆盖父类）
    phase: str = FinancialResearchPhase.SCOPING.value
    
    # 数据收集
    financial_data: List[FinancialData] = field(default_factory=list)
    metrics: Optional[FinancialMetrics] = None
    sentiment: Optional[SentimentData] = None
    
    # 分析结果
    key_findings: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    investment_thesis: Optional[str] = None
    
    # 合规
    disclaimer_added: bool = False


# ==================== FinancialResearchAgent ====================

class FinancialResearchAgent(DeepResearchAgent):
    """金融投研专属 Agent
    
    继承 DeepResearchAgent，扩展以下能力：
    - 六阶段金融研究工作流
    - 集成 FinancialDataTool (OpenBB + AkShare)
    - 财务分析 + 估值分析 + 情绪分析
    - 自动生成合规免责声明
    
    工作流：
    1. 范围界定 → 识别研究类型（个股/行业/宏观）
    2. 数据采集 → 多源并行获取金融数据
    3. 财务分析 → 计算财务指标 + 行业对比
    4. 估值分析 → PE/PB/PS + 历史估值区间
    5. 情绪分析 → 舆情 + 资金流 + 机构观点
    6. 报告生成 → 结构化报告 + 免责声明
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.financial_state: Optional[FinancialResearchState] = None
        
        # 金融关键词检测
        self._financial_keywords = {
            "individual_stock": [
                "股票", "股价", "股份", "stock", "share", "equity",
                "财报", "业绩", "盈利", "营收", "利润",
                "PE", "PB", "估值", "valuation",
                "买入", "卖出", "持有", "投资",
            ],
            "industry": [
                "行业", "sector", "industry",
                "产业链", "上下游", "竞争格局",
                "市场规模", "市占率", "market share",
            ],
            "macro": [
                "宏观", "macro", "GDP", "CPI", "PMI",
                "货币政策", "利率", "通胀",
                "美联储", "央行", "财政政策",
            ]
        }
    
    async def _think(self) -> AsyncGenerator[SSEEvent, None]:
        """思考过程 - 金融研究版本"""
        logger.debug("FinancialResearchAgent thinking...")
        
        phase = self.financial_state.phase if self.financial_state else FinancialResearchPhase.SCOPING.value
        
        # 金融研究阶段性思考提示
        thinking_prompts = {
            FinancialResearchPhase.SCOPING.value: "📊 Identifying research scope: individual stock, industry, or macro analysis...",
            FinancialResearchPhase.COLLECTING.value: "📈 Collecting financial data from multiple sources (OpenBB, AkShare, Browser)...",
            FinancialResearchPhase.ANALYZING.value: "💰 Analyzing financial metrics: profitability, growth, solvency...",
            FinancialResearchPhase.VALUATING.value: "📐 Performing valuation analysis: PE/PB/PS, DCF, industry comparison...",
            FinancialResearchPhase.SENTIMENT.value: "🔥 Analyzing market sentiment: social media, news, capital flow...",
            FinancialResearchPhase.REPORTING.value: "📝 Generating research report with compliance disclaimer...",
        }
        
        yield SSEEvent(
            type=SSEEventType.THINKING,
            data={'content': thinking_prompts.get(phase, "Analyzing financial data...") + "\n"}
        )
        
        # 构造金融专属系统提示
        system_prompt = self._get_financial_thinking_prompt(phase)
        
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
        
        # 更新金融研究状态
        await self._update_financial_state_from_thinking(thinking_content)
        
        logger.debug(f"Financial research thinking complete, phase: {phase}")
    
    def _get_financial_thinking_prompt(self, phase: str) -> str:
        """获取金融研究阶段性思考提示"""
        
        base_prompt = """You are a financial research analyst conducting systematic investment research.

IMPORTANT COMPLIANCE RULES:
- DO NOT provide specific buy/sell recommendations
- DO NOT predict exact stock prices
- DO NOT promise investment returns
- All analysis is for informational purposes only

Current Research State:
"""
        if self.financial_state:
            base_prompt += f"""- Topic: {self.financial_state.topic}
- Scope: {self.financial_state.scope.value}
- Market: {self.financial_state.market.value}
- Symbol: {self.financial_state.symbol or 'Not determined'}
- Phase: {phase}
- Data collected: {len(self.financial_state.financial_data)} items
- Sources: {len(self.financial_state.sources_collected)}
"""
        
        phase_prompts = {
            FinancialResearchPhase.SCOPING.value: """
Analyze the research request and determine:
1. Research scope: individual_stock / industry / macro / thematic
2. Target market: us / cn / hk / global
3. Stock symbol(s) or industry name
4. Key aspects to investigate (fundamentals, valuation, sentiment)

Output a clear research plan.""",

            FinancialResearchPhase.COLLECTING.value: """
Plan data collection strategy:
1. Use financial_data tool for structured data (quotes, financials, valuation)
2. Use web_search for news and analysis reports
3. Use browser for detailed pages (company announcements, filings)

Prioritize authoritative sources:
- US: SEC filings, Yahoo Finance, Bloomberg
- CN: 巨潮资讯, 东方财富, 同花顺
- HK: HKEX announcements

Focus on getting: quote, fundamental, valuation, news data.""",

            FinancialResearchPhase.ANALYZING.value: """
Analyze the collected financial data:
1. Profitability: ROE, ROA, Gross Margin, Net Margin
2. Growth: Revenue Growth, Profit Growth YoY
3. Solvency: Debt Ratio, Current Ratio
4. Cash Flow: Operating CF, Free CF

Compare with industry averages if available.
Identify strengths and weaknesses.""",

            FinancialResearchPhase.VALUATING.value: """
Perform valuation analysis:
1. Relative valuation: PE, PB, PS, EV/EBITDA
2. Compare with industry peers
3. Historical valuation range (past 5 years)
4. Assess if current valuation is high/fair/low

DO NOT provide specific price targets - only assess valuation level.""",

            FinancialResearchPhase.SENTIMENT.value: """
Analyze market sentiment:
1. News sentiment (positive/neutral/negative)
2. Social media discussions (if available)
3. Analyst ratings and target prices (as reference)
4. Capital flow indicators (for A-stocks: 北向资金, 融资融券)

Summarize overall market sentiment.""",

            FinancialResearchPhase.REPORTING.value: """
Generate the final research report with:

1. **Executive Summary** (2-3 sentences)
2. **Company Overview** (if applicable)
3. **Financial Analysis**
   - Key metrics with industry comparison
4. **Valuation Analysis**
   - Current valuation vs historical/peers
5. **Market Sentiment**
   - News and social sentiment summary
6. **Risk Factors** (MANDATORY)
   - List 3-5 key risks
7. **References** (with citations)
8. **Disclaimer** (MANDATORY)

IMPORTANT: Include the compliance disclaimer at the end."""
        }
        
        return base_prompt + phase_prompts.get(phase, "Continue research based on current needs.")
    
    async def _update_financial_state_from_thinking(self, thinking: str) -> None:
        """从思考内容更新金融研究状态"""
        if not self.financial_state:
            return
        
        # 检测研究范围
        if self.financial_state.phase == FinancialResearchPhase.SCOPING.value:
            # 识别股票代码
            symbol = self._extract_symbol_from_thinking(thinking)
            if symbol:
                self.financial_state.symbol = symbol
                
            # 识别市场
            market = self._detect_market(thinking)
            self.financial_state.market = market
            
            # 识别研究范围
            scope = self._detect_scope(thinking)
            self.financial_state.scope = scope
    
    def _extract_symbol_from_thinking(self, thinking: str) -> Optional[str]:
        """从思考内容提取股票代码"""
        # 美股代码 (1-5个字母)
        us_pattern = r'\b([A-Z]{1,5})\b'
        # A股代码 (6位数字)
        cn_pattern = r'\b(\d{6})\b'
        # 港股代码 (1-5位数字)
        hk_pattern = r'\b(\d{1,5})\.HK\b'
        
        # 优先检测明确的股票代码上下文
        context_patterns = [
            r'(?:symbol|code|股票代码|stock)[:\s]+([A-Z0-9\.]{2,10})',
            r'([A-Z]{1,5})\s+(?:stock|shares)',
            r'(\d{6})(?:\.SH|\.SZ|\.SS)?',
        ]
        
        for pattern in context_patterns:
            match = re.search(pattern, thinking, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        return None
    
    def _detect_market(self, thinking: str) -> Market:
        """检测目标市场"""
        thinking_lower = thinking.lower()
        
        # A股关键词
        cn_keywords = ["a股", "a-stock", "上交所", "深交所", "sse", "szse", "沪深", "a share"]
        if any(kw in thinking_lower for kw in cn_keywords):
            return Market.CN
        
        # 6位数字代码
        if re.search(r'\b\d{6}\b', thinking):
            return Market.CN
        
        # 港股关键词
        hk_keywords = ["港股", "hk stock", "hkex", "恒生"]
        if any(kw in thinking_lower for kw in hk_keywords):
            return Market.HK
        
        # 默认美股
        return Market.US
    
    def _detect_scope(self, thinking: str) -> ResearchScope:
        """检测研究范围"""
        thinking_lower = thinking.lower()
        
        # 行业研究
        for kw in self._financial_keywords["industry"]:
            if kw.lower() in thinking_lower:
                return ResearchScope.INDUSTRY
        
        # 宏观研究
        for kw in self._financial_keywords["macro"]:
            if kw.lower() in thinking_lower:
                return ResearchScope.MACRO
        
        # 默认个股研究
        return ResearchScope.INDIVIDUAL_STOCK
    
    async def _decide(self) -> AgentAction:
        """决策 - 金融研究版本"""
        logger.debug(f"FinancialResearchAgent deciding, phase: {self.financial_state.phase if self.financial_state else 'init'}")
        
        # 初始化金融研究状态
        if not self.financial_state:
            topic = self._extract_topic_from_context()
            self.financial_state = FinancialResearchState(topic=topic)
            # 也设置父类的 research_state
            self.research_state = self.financial_state
            logger.info(f"Financial research initialized for topic: {topic}")
        
        # 获取可用工具
        tool_definitions = self.tools.get_llm_tool_definitions()
        
        if not tool_definitions:
            logger.warning("No tools available, generating report directly")
            return await self._generate_financial_report()
        
        # 根据阶段决定系统提示
        system_prompt = self._get_financial_decision_prompt()
        
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
            if self._action_count >= 2 and tool_call["name"] in ["web_search", "read_url", "financial_data", "browser_open"]:
                self._action_count = 0
                await self._record_financial_findings()
            
            # 更新阶段
            self._update_financial_phase_from_tool(tool_call["name"])
            
            return AgentAction(
                type=ActionType.TOOL_CALL,
                tool_name=tool_call["name"],
                tool_input=tool_call["input"],
                tool_call_id=tool_call["id"]
            )
        
        # 检查是否应该生成报告
        if self._should_generate_financial_report():
            return await self._generate_financial_report()
        
        # 默认继续研究
        answer = response.content.strip()
        return AgentAction(
            type=ActionType.ANSWER,
            answer=answer
        )
    
    def _get_financial_decision_prompt(self) -> str:
        """获取金融研究决策提示"""
        phase = self.financial_state.phase if self.financial_state else FinancialResearchPhase.SCOPING.value
        
        base = """You are conducting financial research. Based on the conversation and your analysis:

Available tools:
- financial_data: Get financial data (quote, fundamental, valuation, news) for stocks
  - For US stocks: Use symbol like "AAPL", "MSFT"
  - For A-stocks: Use 6-digit code like "600519", "000001"
- web_search: Search for financial news and analysis
- read_url: Read full content from financial websites
- browser_open: Open pages with interactive elements

COMPLIANCE RULES:
- Do NOT provide buy/sell recommendations
- Do NOT predict specific prices
- Focus on factual data and analysis

Current research state:
"""
        if self.financial_state:
            base += f"""- Topic: {self.financial_state.topic}
- Scope: {self.financial_state.scope.value}
- Market: {self.financial_state.market.value}
- Symbol: {self.financial_state.symbol or 'Not determined'}
- Phase: {phase}
- Data items: {len(self.financial_state.financial_data)}
- Sources: {len(self.financial_state.sources_collected)}
"""
        
        phase_instructions = {
            FinancialResearchPhase.SCOPING.value: """
You are starting financial research. First action:
1. If symbol is not determined, use web_search to identify the company/stock
2. Once you have the symbol, use financial_data to get quote data
3. Plan the research approach based on scope (individual/industry/macro)

Do NOT generate a final answer yet - gather data first.""",

            FinancialResearchPhase.COLLECTING.value: """
Collect financial data systematically:
1. Use financial_data with data_type="quote" for real-time price
2. Use financial_data with data_type="fundamental" for financial statements
3. Use financial_data with data_type="valuation" for PE/PB/PS
4. Use web_search for recent news and analyst reports

Prioritize structured data over web scraping.""",

            FinancialResearchPhase.ANALYZING.value: """
You have basic data. Now analyze:
1. If fundamental data is incomplete, fetch more using financial_data
2. Use web_search to find industry comparison data
3. Calculate key ratios if not provided

Focus on ROE, margins, growth rates.""",

            FinancialResearchPhase.VALUATING.value: """
Perform valuation analysis:
1. If valuation data is incomplete, fetch using financial_data
2. Search for peer comparison using web_search
3. Look for historical valuation range

Do NOT give specific price targets.""",

            FinancialResearchPhase.SENTIMENT.value: """
Analyze market sentiment:
1. Use web_search for recent news sentiment
2. If A-stock, use financial_data for capital flow (北向资金)
3. Search for analyst ratings

Once you have enough data, move to reporting.""",

            FinancialResearchPhase.REPORTING.value: """
Generate the final research report now.
Include all citations, financial metrics, and a MANDATORY disclaimer.
Do NOT call any more tools - provide the complete answer."""
        }
        
        return base + phase_instructions.get(phase, "Continue research based on current needs.")
    
    def _update_financial_phase_from_tool(self, tool_name: str) -> None:
        """根据工具调用更新金融研究阶段"""
        if not self.financial_state:
            return
        
        current_phase = self.financial_state.phase
        
        if tool_name == "financial_data":
            # 金融数据工具调用推动阶段前进
            if current_phase == FinancialResearchPhase.SCOPING.value:
                self.financial_state.phase = FinancialResearchPhase.COLLECTING.value
            elif current_phase == FinancialResearchPhase.COLLECTING.value:
                # 检查是否收集了足够数据
                if len(self.financial_state.financial_data) >= 3:
                    self.financial_state.phase = FinancialResearchPhase.ANALYZING.value
        
        elif tool_name == "web_search":
            if current_phase == FinancialResearchPhase.SCOPING.value:
                self.financial_state.phase = FinancialResearchPhase.COLLECTING.value
            elif current_phase == FinancialResearchPhase.ANALYZING.value:
                self.financial_state.phase = FinancialResearchPhase.VALUATING.value
            elif current_phase == FinancialResearchPhase.VALUATING.value:
                self.financial_state.phase = FinancialResearchPhase.SENTIMENT.value
        
        elif tool_name in ["read_url", "browser_open"]:
            if current_phase in [FinancialResearchPhase.SCOPING.value, FinancialResearchPhase.COLLECTING.value]:
                self.financial_state.phase = FinancialResearchPhase.COLLECTING.value
        
        # 检查是否应该进入报告阶段
        if self._should_generate_financial_report():
            self.financial_state.phase = FinancialResearchPhase.REPORTING.value
    
    def _should_generate_financial_report(self) -> bool:
        """判断是否应该生成金融报告"""
        if not self.financial_state:
            return False
        
        # 已经在报告阶段
        if self.financial_state.phase == FinancialResearchPhase.REPORTING.value:
            return True
        
        # 收集了足够数据
        if (len(self.financial_state.financial_data) >= 4 and 
            len(self.financial_state.sources_collected) >= 3):
            self.financial_state.phase = FinancialResearchPhase.REPORTING.value
            return True
        
        # 迭代次数过多
        if self.financial_state.iteration > 20:
            self.financial_state.phase = FinancialResearchPhase.REPORTING.value
            return True
        
        return False
    
    async def _generate_financial_report(self) -> AgentAction:
        """生成金融研究报告"""
        logger.info("Generating financial research report...")
        
        # 构造报告生成提示
        system_prompt = """Generate a comprehensive financial research report.

STRUCTURE:
1. **Executive Summary** (2-3 sentences)
2. **Company Overview** (if individual stock)
3. **Financial Analysis**
   - Key Metrics Table (ROE, Margins, Growth, etc.)
   - Industry Comparison (if available)
4. **Valuation Analysis**
   - Current PE/PB/PS
   - Historical Range (if available)
   - Peer Comparison (if available)
5. **Market Sentiment**
   - Recent News Summary
   - Capital Flow (for A-stocks)
6. **Risk Factors** (MANDATORY - list 3-5 key risks)
7. **References** (numbered citations)

---

**⚠️ Disclaimer** (MANDATORY)

本报告仅为信息整合与分析参考，**不构成任何投资建议**。
投资有风险，入市需谨慎。用户应自行判断并承担投资决策后果。
本报告数据来源于公开渠道，TokenDance 不对数据准确性负责。

This report is for informational purposes only and does NOT constitute investment advice.
Investing involves risk. Users should make their own judgments and bear the consequences.

---

Use markdown formatting. Every factual claim MUST have a citation."""
        
        # 添加收集的数据到上下文
        data_context = self._format_financial_data_for_report()
        
        messages = self.context.messages.copy()
        messages.append({
            "role": "user",
            "content": f"Based on the collected data, generate the final financial research report.\n\n{data_context}"
        })
        
        response = await self.llm.complete(
            messages=messages,
            system=system_prompt
        )
        
        report = response.content.strip()
        
        # 确保添加引用部分
        if self.financial_state and self.financial_state.sources_collected:
            if "## References" not in report and "## 参考来源" not in report:
                report += "\n\n---\n\n## References\n\n"
                for i, source in enumerate(self.financial_state.sources_collected, 1):
                    report += source.to_citation(i) + "\n"
        
        # 确保添加免责声明
        if "Disclaimer" not in report and "免责声明" not in report:
            report += self._get_disclaimer()
        
        # 记录到 findings.md
        try:
            await self.memory.write_findings(
                f"Financial Research Report - {self.financial_state.symbol or self.financial_state.topic[:30]}",
                report[:3000]  # 摘要
            )
        except Exception as e:
            logger.warning(f"Failed to record findings: {e}")
        
        self.financial_state.phase = FinancialResearchPhase.REPORTING.value
        self.financial_state.disclaimer_added = True
        
        return AgentAction(
            type=ActionType.ANSWER,
            answer=report
        )
    
    def _format_financial_data_for_report(self) -> str:
        """格式化金融数据用于报告生成"""
        if not self.financial_state:
            return "No data collected yet."
        
        formatted = "## Collected Financial Data\n\n"
        
        # 基本信息
        formatted += f"**Symbol**: {self.financial_state.symbol or 'N/A'}\n"
        formatted += f"**Market**: {self.financial_state.market.value}\n"
        formatted += f"**Scope**: {self.financial_state.scope.value}\n\n"
        
        # 金融数据
        for i, data in enumerate(self.financial_state.financial_data, 1):
            formatted += f"### Data Source {i}: {data.source} - {data.data_type}\n"
            formatted += f"```json\n{str(data.data)[:1000]}\n```\n\n"
        
        # 来源列表
        if self.financial_state.sources_collected:
            formatted += "### Web Sources\n"
            for i, source in enumerate(self.financial_state.sources_collected, 1):
                formatted += f"[{i}] {source.title} ({source.credibility.value})\n"
                formatted += f"    URL: {source.url}\n"
                if source.snippet:
                    formatted += f"    Summary: {source.snippet[:200]}...\n"
        
        return formatted
    
    def _get_disclaimer(self) -> str:
        """获取免责声明"""
        return """

---

## ⚠️ 免责声明 / Disclaimer

本报告仅为信息整合与分析参考，**不构成任何投资建议**。投资有风险，入市需谨慎。用户应自行判断并承担投资决策后果。本报告数据来源于公开渠道，TokenDance 不对数据准确性负责。

This report is for informational purposes only and does NOT constitute investment advice. Investing involves risk. Users should make their own judgments and bear the consequences of their investment decisions. Data in this report comes from public sources, and TokenDance is not responsible for data accuracy.

---

*Report generated by TokenDance Financial Research Agent*
"""
    
    async def _record_financial_findings(self) -> None:
        """记录金融发现到 findings.md (2-Action Rule)"""
        if not self.financial_state:
            return
        
        summary = f"Financial Research Progress\n"
        summary += f"- Phase: {self.financial_state.phase}\n"
        summary += f"- Symbol: {self.financial_state.symbol}\n"
        summary += f"- Market: {self.financial_state.market.value}\n"
        summary += f"- Data items: {len(self.financial_state.financial_data)}\n"
        summary += f"- Web sources: {len(self.financial_state.sources_collected)}\n"
        
        try:
            await self.memory.write_findings(
                f"Financial Research Update ({self.financial_state.topic[:50]})",
                summary
            )
        except Exception as e:
            logger.warning(f"Failed to record findings: {e}")
    
    def add_financial_data(self, data_type: str, source: str, data: Dict[str, Any]) -> None:
        """添加金融数据"""
        if not self.financial_state:
            return
        
        financial_data = FinancialData(
            data_type=data_type,
            source=source,
            data=data
        )
        self.financial_state.financial_data.append(financial_data)
        logger.info(f"Added financial data: {data_type} from {source}")


# ==================== 工厂函数 ====================

async def create_financial_research_agent(
    context,
    llm,
    tools,
    memory,
    db,
    max_iterations: int = 30,
    max_sources: int = 15
) -> FinancialResearchAgent:
    """创建 FinancialResearchAgent 实例
    
    Args:
        context: AgentContext
        llm: BaseLLM
        tools: ToolRegistry
        memory: WorkingMemory
        db: AsyncSession
        max_iterations: 最大迭代次数
        max_sources: 最大来源数
        
    Returns:
        FinancialResearchAgent: Agent 实例
    """
    agent = FinancialResearchAgent(
        context=context,
        llm=llm,
        tools=tools,
        memory=memory,
        db=db,
        max_iterations=max_iterations
    )
    
    # 初始化研究状态参数
    if agent.research_state:
        agent.research_state.max_sources = max_sources
    
    logger.info(f"FinancialResearchAgent created with max_iterations={max_iterations}, max_sources={max_sources}")
    return agent
