"""
Financial API endpoints.

Provides HTTP endpoints for financial data and sentiment analysis.
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agent.tools.builtin.financial import FinancialDataTool
from app.agent.tools.builtin.financial.sentiment import get_sentiment_tool


# 懒加载分析服务
def _get_financial_analyzer():
    from app.services.financial import get_financial_analyzer
    return get_financial_analyzer()

def _get_valuation_analyzer():
    from app.services.financial import get_valuation_analyzer
    return get_valuation_analyzer()

def _get_technical_indicators():
    from app.services.financial import get_technical_indicators
    return get_technical_indicators()


def _get_industry_benchmark_service():
    from app.services.financial.benchmark import get_industry_benchmark_service
    return get_industry_benchmark_service()


def _get_peer_comparison_service():
    from app.services.financial.industry import get_peer_comparison_service
    return get_peer_comparison_service()


router = APIRouter()


# ==================== Request/Response Models ====================

class StockInfoRequest(BaseModel):
    """Request for stock info."""
    symbol: str = Field(..., description="Stock symbol (e.g., '600519')")


class StockQuoteRequest(BaseModel):
    """Request for stock quote."""
    symbol: str = Field(..., description="Stock symbol")


class HistoricalDataRequest(BaseModel):
    """Request for historical data."""
    symbol: str = Field(..., description="Stock symbol")
    start_date: str | None = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: str | None = Field(None, description="End date (YYYY-MM-DD)")
    period: str | None = Field("1d", description="Period (1d, 1wk, 1mo)")


class SentimentAnalyzeRequest(BaseModel):
    """Request for sentiment analysis."""
    symbol: str = Field(..., description="Stock symbol")
    sources: list[str] | None = Field(None, description="Sources (xueqiu, guba)")
    limit_per_source: int = Field(20, description="Posts limit per source", ge=1, le=100)
    analyze: bool = Field(True, description="Whether to analyze sentiment")


class SentimentSearchRequest(BaseModel):
    """Request for sentiment search."""
    query: str = Field(..., description="Search query")
    sources: list[str] | None = Field(None, description="Sources to search")
    limit: int = Field(20, description="Maximum posts", ge=1, le=100)


class CombinedAnalysisRequest(BaseModel):
    """Request for combined analysis."""
    symbol: str = Field(..., description="Stock symbol")
    sentiment_sources: list[str] | None = Field(None, description="Sentiment sources")
    sentiment_limit: int = Field(20, description="Sentiment posts limit", ge=1, le=100)
    historical_days: int = Field(30, description="Historical data days", ge=1, le=365)


class AnalysisRequest(BaseModel):
    """分析引擎请求"""
    symbol: str = Field(..., description="股票代码 (e.g., '600519', 'AAPL')")
    market: str | None = Field(None, description="市场 (cn/us/hk)。若不提供则自动识别")


class ComprehensiveAnalysisRequest(BaseModel):
    """综合分析请求"""
    symbol: str = Field(..., description="股票代码")
    market: str | None = Field(None, description="市场")
    include_technical: bool = Field(True, description="是否包含技术分析")


class PercentileRequest(BaseModel):
    """行业分位数请求"""
    symbol: str = Field(..., description="股票代码 (e.g., '600519')")
    metrics: list[str] | None = Field(
        None,
        description="指标列表 (默认: roe, net_margin, revenue_growth, pe_ttm, debt_ratio)"
    )
    include_dupont: bool = Field(True, description="是否包含 DuPont 分解")


class PeerMatrixRequest(BaseModel):
    """同行对比矩阵请求"""
    symbol: str = Field(..., description="股票代码")
    peer_count: int = Field(3, description="对比公司数量", ge=1, le=10)
    custom_peers: list[str] | None = Field(None, description="自定义对比公司列表")


# ==================== Endpoints ====================

@router.post("/stock/info")
async def get_stock_info(request: StockInfoRequest):
    """
    Get stock basic information.

    Returns:
    - name: Stock name
    - market: Market code
    - price: Latest price
    - market_cap: Market capitalization
    - ...
    """
    try:
        tool = FinancialDataTool()
        result = await tool.get_stock_info(request.symbol)

        if not result.get("success"):
            raise HTTPException(
                status_code=404,
                detail=result.get("error", "Stock not found")
            )

        return {
            "success": True,
            "data": result.get("data"),
            "disclaimer": result.get("disclaimer", "")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/stock/quote")
async def get_stock_quote(request: StockQuoteRequest):
    """
    Get stock real-time quote.

    Returns:
    - current_price: Current price
    - change_percent: Change percentage
    - open: Today's open
    - high: Today's high
    - low: Today's low
    - volume: Trading volume
    """
    try:
        tool = FinancialDataTool()
        result = await tool.get_quote(request.symbol)

        if not result.get("success"):
            raise HTTPException(
                status_code=404,
                detail=result.get("error", "Quote not found")
            )

        return {
            "success": True,
            "data": result.get("data"),
            "disclaimer": result.get("disclaimer", "")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/stock/historical")
async def get_historical_data(request: HistoricalDataRequest):
    """
    Get stock historical data.

    Returns:
    - records: List of historical records
        - date: Date
        - open: Open price
        - high: High price
        - low: Low price
        - close: Close price
        - volume: Volume
    """
    try:
        tool = FinancialDataTool()
        result = await tool.get_historical(
            request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            period=request.period,
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=404,
                detail=result.get("error", "Historical data not found")
            )

        return {
            "success": True,
            "data": result.get("data"),
            "disclaimer": result.get("disclaimer", "")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/sentiment/analyze")
async def analyze_sentiment(request: SentimentAnalyzeRequest):
    """
    Analyze stock sentiment from social media.

    Returns:
    - analysis: Sentiment analysis result
        - overall_label: bullish / bearish / neutral
        - overall_score: -1 (bearish) to 1 (bullish)
        - confidence: 0 to 1
        - bullish_count: Number of bullish posts
        - bearish_count: Number of bearish posts
        - neutral_count: Number of neutral posts
        - key_bullish_points: Key bullish arguments
        - key_bearish_points: Key bearish arguments
    - posts: List of crawled posts
    - sources_used: Sources successfully crawled
    """
    try:
        tool = get_sentiment_tool()

        result = await tool.analyze(
            request.symbol,
            sources=request.sources,
            limit_per_source=request.limit_per_source,
            analyze=request.analyze,
        )

        return {
            "success": result.success,
            "data": result.to_dict(),
            "errors": result.errors if result.errors else [],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/sentiment/search")
async def search_sentiment(request: SentimentSearchRequest):
    """
    Search for posts matching query.

    Returns:
    - posts: List of matching posts
    - analysis: Sentiment analysis
    """
    try:
        tool = get_sentiment_tool()

        result = await tool.search(
            request.query,
            sources=request.sources,
            limit=request.limit,
        )

        return {
            "success": result.success,
            "data": result.to_dict(),
            "errors": result.errors if result.errors else [],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/combined")
async def combined_analysis(request: CombinedAnalysisRequest):
    """
    Combined analysis: financial data + sentiment.

    Returns:
    - stock_info: Basic information
    - quote: Real-time quote
    - historical: Historical data
    - sentiment: Sentiment analysis
    """
    try:
        data_tool = FinancialDataTool()
        sentiment_tool = get_sentiment_tool()

        # Get financial data
        info_result = await data_tool.get_stock_info(request.symbol)
        quote_result = await data_tool.get_quote(request.symbol)

        # Get historical data
        from datetime import timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=request.historical_days)

        hist_result = await data_tool.get_historical(
            request.symbol,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
        )

        # Get sentiment
        sentiment_result = await sentiment_tool.analyze(
            request.symbol,
            sources=request.sentiment_sources,
            limit_per_source=request.sentiment_limit,
        )

        return {
            "success": True,
            "data": {
                "stock_info": info_result.get("data") if info_result.get("success") else None,
                "quote": quote_result.get("data") if quote_result.get("success") else None,
                "historical": hist_result.get("data") if hist_result.get("success") else None,
                "sentiment": sentiment_result.to_dict() if sentiment_result.success else None,
            },
            "errors": {
                "stock_info": None if info_result.get("success") else info_result.get("error"),
                "quote": None if quote_result.get("success") else quote_result.get("error"),
                "historical": None if hist_result.get("success") else hist_result.get("error"),
                "sentiment": sentiment_result.errors if not sentiment_result.success else [],
            },
            "disclaimer": info_result.get("disclaimer", "")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "financial",
        "timestamp": datetime.now().isoformat()
    }


# ==================== 分析引擎 API ====================

@router.post("/analysis/financial")
async def run_financial_analysis(request: AnalysisRequest):
    """
    运行财务分析。

    分析维度:
    - 盈利能力 (ROE, ROA, 毛利率, 净利率)
    - 成长能力 (营收增速, 利润增速)
    - 偿债能力 (资产负债率, 流动比率, 速动比率)
    - 运营效率 (应收周转, 存货周转)
    - 现金流 (经营现金流, 自由现金流)

    Returns:
    - overall_score: 综合评分 (0-100)
    - health_level: 健康度等级
    - dimension_scores: 各维度得分
    - strengths: 优势
    - key_risks: 风险
    """
    try:
        analyzer = _get_financial_analyzer()
        market = request.market or _detect_market(request.symbol)

        result = await analyzer.analyze(
            symbol=request.symbol,
            market=market
        )

        return {
            "success": True,
            "data": result.to_dict(),
            "disclaimer": "本分析仅供参考，不构成投资建议。"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/analysis/valuation")
async def run_valuation_analysis(request: AnalysisRequest):
    """
    运行估值分析。

    分析内容:
    - 相对估值 (PE/PB/PS/EV-EBITDA/PEG)
    - 历史估值对比
    - 行业估值对比
    - DCF 简化模型

    Returns:
    - valuation_level: 估值水平 (extremely_low/low/fair/high/extremely_high)
    - current_price: 当前价格
    - target_price_range: 目标价格区间
    - key_points: 关键点
    - risks: 风险提示
    """
    try:
        analyzer = _get_valuation_analyzer()
        market = request.market or _detect_market(request.symbol)

        result = await analyzer.analyze(
            symbol=request.symbol,
            market=market
        )

        return {
            "success": True,
            "data": result.to_dict(),
            "disclaimer": "估值分析仅供参考，不代表任何价格预测。"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/analysis/technical")
async def run_technical_analysis(request: AnalysisRequest):
    """
    运行技术分析。

    分析指标:
    - 趋势指标 (MACD, SMA/EMA, ADX)
    - 动量指标 (RSI, KDJ, Williams %R, CCI)
    - 波动率指标 (布林带, ATR)
    - 成交量指标 (OBV)

    Returns:
    - overall_signal: 综合信号 (strong_buy/buy/neutral/sell/strong_sell)
    - score: 技术评分 (0-100)
    - buy_signals: 买入信号
    - sell_signals: 卖出信号
    - support_levels: 支撑位
    - resistance_levels: 阻力位
    """
    try:
        service = _get_technical_indicators()
        market = request.market or _detect_market(request.symbol)

        result = await service.analyze(
            symbol=request.symbol,
            market=market
        )

        return {
            "success": True,
            "data": result.to_dict(),
            "disclaimer": "技术分析仅供参考，历史表现不代表未来结果。"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/analysis/comprehensive")
async def run_comprehensive_analysis(request: ComprehensiveAnalysisRequest):
    """
    运行综合分析（财务 + 估值 + 技术）。

    使用并行执行和缓存优化，将总耗时从 T1+T2+T3 优化为 max(T1,T2,T3)。

    Returns:
    - financial: 财务分析结果
    - valuation: 估值分析结果
    - technical: 技术分析结果 (若 include_technical=true)
    - summary: 综合摘要
    - elapsed_seconds: 执行耗时
    - cache_hits: 缓存命中列表
    """
    try:
        from app.services.financial.cache import run_parallel_analysis

        market = request.market or _detect_market(request.symbol)

        # 使用优化的并行分析
        results = await run_parallel_analysis(
            symbol=request.symbol,
            market=market,
            include_technical=request.include_technical,
            use_cache=True,  # 启用缓存
        )

        return {
            "success": True,
            "data": results,
            "disclaimer": "本分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ==================== 行业基准 & 同行对比 API ====================

@router.post("/benchmark/percentile")
async def get_industry_percentile(request: PercentileRequest):
    """
    获取指标行业分位数。

    每个指标返回：
    - percentile: TOP X% (越小越好)
    - current_value: 当前值
    - mean: 行业均值
    - percentile_50: 行业中位数
    - rank: 排名
    - trend_description: 趋势描述

    可选 DuPont 分解：
    - net_profit_margin: 净利率
    - asset_turnover: 资产周转率
    - equity_multiplier: 权益乘数
    - primary_driver: 主要驱动因素
    - insights: 分析洞察
    """
    try:
        service = _get_industry_benchmark_service()

        # 获取分位数
        benchmarks = await service.get_multiple_percentiles(
            symbol=request.symbol,
            metrics=request.metrics,
        )

        result = {
            "symbol": request.symbol,
            "benchmarks": [b.to_dict() for b in benchmarks],
        }

        # 可选 DuPont 分解
        if request.include_dupont:
            dupont = await service.get_dupont_decomposition(request.symbol)
            result["dupont"] = dupont.to_dict()

        return {
            "success": True,
            "data": result,
            "disclaimer": "行业分位数基于同行业公司对比，仅供参考。"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/peer/matrix")
async def get_peer_comparison_matrix(request: PeerMatrixRequest):
    """
    获取同行对比矩阵 (PK 矩阵)。

    返回：
    - peers: 对比公司列表
    - metrics: 各指标对比
        - metric_name: 指标名
        - values: 各公司的值
        - winner: 冠军 (symbol)
        - industry_mean: 行业均值
    - scores: 综合评分 (0-100)
    - insights: 分析洞察
    """
    try:
        service = _get_peer_comparison_service()

        matrix = await service.get_comparison_matrix(
            symbol=request.symbol,
            peer_count=request.peer_count,
            custom_peers=request.custom_peers,
        )

        return {
            "success": True,
            "data": matrix.to_dict(),
            "disclaimer": "同行对比仅供参考，不同公司的业务模式可能存在差异。"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ==================== 事件日历 API ====================

class EventCalendarRequest(BaseModel):
    """事件日历请求"""
    symbol: str = Field(..., description="股票代码")
    days_ahead: int = Field(90, description="未来天数", ge=1, le=365)
    event_types: list[str] | None = Field(None, description="筛选事件类型")
    min_importance: str = Field("low", description="最低重要性: low/medium/high/critical")


class HistoricalImpactRequest(BaseModel):
    """历史事件影响请求"""
    symbol: str = Field(..., description="股票代码")
    event_type: str = Field(..., description="事件类型")
    lookback_events: int = Field(8, description="回看事件数量", ge=1, le=20)


def _get_event_calendar_service():
    """懒加载 EventCalendarService"""
    from app.services.financial.event import get_event_calendar_service
    return get_event_calendar_service()


@router.post("/events/upcoming")
async def get_upcoming_events(request: EventCalendarRequest):
    """
    获取股票未来事件日历。

    返回：
    - upcoming_events: 事件列表
        - event_type: 事件类型 (earnings/dividend/equity_unlock/...)
        - event_date: 事件日期
        - importance: 重要性 (low/medium/high/critical)
        - title: 事件标题
        - description: 事件描述
        - days_until: 距今天数
        - historical_impact: 历史类似事件影响
    - events_by_type: 按类型分组统计
    - next_critical_event: 最近的重要事件
    - avg_post_event_return: 历史事件后平均收益
    """
    try:
        from app.services.financial.event import EventImportance, EventType

        service = _get_event_calendar_service()

        # 解析事件类型筛选
        event_type_filters = None
        if request.event_types:
            event_type_filters = []
            for et in request.event_types:
                try:
                    event_type_filters.append(EventType(et))
                except ValueError:
                    pass  # 忽略无效类型

        # 解析最低重要性
        try:
            min_imp = EventImportance(request.min_importance)
        except ValueError:
            min_imp = EventImportance.LOW

        result = await service.get_upcoming_events(
            symbol=request.symbol,
            days_ahead=request.days_ahead,
            event_types=event_type_filters,
            min_importance=min_imp,
        )

        return {
            "success": True,
            "data": result.to_dict(),
            "disclaimer": "事件日期为预估值，实际日期以公司公告为准。"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/events/historical-impact")
async def get_historical_event_impact(request: HistoricalImpactRequest):
    """
    获取历史事件影响分析。

    返回：
    - impacts: 历史事件影响列表
        - event_date: 事件日期
        - price_change_1d/5d/20d: 事件后涨跌幅 %
        - excess_return_1d/5d: 相对指数超额收益 %
        - volume_change_pct: 成交量变化 %
        - direction: 影响方向 (positive/negative/neutral)
    """
    try:
        from app.services.financial.event import EventType

        service = _get_event_calendar_service()

        # 解析事件类型
        try:
            event_type = EventType(request.event_type)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event_type: {request.event_type}"
            ) from e

        impacts = await service.get_historical_event_impact(
            symbol=request.symbol,
            event_type=event_type,
            lookback_events=request.lookback_events,
        )

        return {
            "success": True,
            "data": {
                "symbol": request.symbol,
                "event_type": request.event_type,
                "impacts": [i.to_dict() for i in impacts],
            },
            "disclaimer": "历史表现不代表未来收益。"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


def _detect_market(symbol: str) -> str:
    """根据股票代码识别市场"""
    import re

    # 6位数字 = A股
    if re.match(r'^\d{6}$', symbol):
        return 'cn'

    # 1-5位数字 + .HK = 港股
    if re.match(r'^\d{1,5}\.HK$', symbol.upper()):
        return 'hk'

    # 1-5位字母 = 美股
    if re.match(r'^[A-Z]{1,5}$', symbol.upper()):
        return 'us'

    # 默认返回 A 股
    return 'cn'
