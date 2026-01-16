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
