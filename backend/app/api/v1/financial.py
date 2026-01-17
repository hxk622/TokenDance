"""
Financial API endpoints.

Provides HTTP endpoints for financial data and sentiment analysis.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

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
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    period: Optional[str] = Field("1d", description="Period (1d, 1wk, 1mo)")


class SentimentAnalyzeRequest(BaseModel):
    """Request for sentiment analysis."""
    symbol: str = Field(..., description="Stock symbol")
    sources: Optional[list[str]] = Field(None, description="Sources (xueqiu, guba)")
    limit_per_source: int = Field(20, description="Posts limit per source", ge=1, le=100)
    analyze: bool = Field(True, description="Whether to analyze sentiment")


class SentimentSearchRequest(BaseModel):
    """Request for sentiment search."""
    query: str = Field(..., description="Search query")
    sources: Optional[list[str]] = Field(None, description="Sources to search")
    limit: int = Field(20, description="Maximum posts", ge=1, le=100)


class CombinedAnalysisRequest(BaseModel):
    """Request for combined analysis."""
    symbol: str = Field(..., description="Stock symbol")
    sentiment_sources: Optional[list[str]] = Field(None, description="Sentiment sources")
    sentiment_limit: int = Field(20, description="Sentiment posts limit", ge=1, le=100)
    historical_days: int = Field(30, description="Historical data days", ge=1, le=365)


class AnalysisRequest(BaseModel):
    """分析引擎请求"""
    symbol: str = Field(..., description="股票代码 (e.g., '600519', 'AAPL')")
    market: Optional[str] = Field(None, description="市场 (cn/us/hk)。若不提供则自动识别")


class ComprehensiveAnalysisRequest(BaseModel):
    """综合分析请求"""
    symbol: str = Field(..., description="股票代码")
    market: Optional[str] = Field(None, description="市场")
    include_technical: bool = Field(True, description="是否包含技术分析")


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
