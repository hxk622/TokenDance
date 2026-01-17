"""
FinancialDataTool - Unified interface for financial data.

This tool routes requests to appropriate data adapters based on:
- Market (US, CN, HK)
- Data type (quote, historical, fundamental, etc.)
- Compliance rules

Usage:
    tool = FinancialDataTool()

    # US Stock
    result = await tool.execute(symbol="AAPL", data_type="quote", market="us")

    # A-Stock
    result = await tool.execute(symbol="600519", data_type="quote", market="cn")
"""

from typing import Literal

from app.agent.tools.builtin.financial.adapters.akshare_adapter import AkShareAdapter
from app.agent.tools.builtin.financial.adapters.base import (
    FinancialDataResult,
    Market,
)
from app.agent.tools.builtin.financial.adapters.openbb_adapter import OpenBBAdapter
from app.agent.tools.builtin.financial.compliance import get_compliance_checker


class FinancialDataTool:
    """
    Unified financial data tool.

    Routes data requests to appropriate adapters based on market and data type.
    Enforces compliance rules for all data access.
    """

    name = "financial_data"
    description = """获取金融市场数据，支持美股、A股、港股。

数据类型:
- quote: 实时行情
- historical: 历史价格
- fundamental: 财务报表
- valuation: 估值指标 (PE/PB/PS)
- news: 财经新闻
- sentiment: 市场舆情

市场:
- us: 美股 (使用 OpenBB)
- cn: A股 (使用 AkShare)
- hk: 港股

示例:
- 获取苹果股价: symbol="AAPL", data_type="quote", market="us"
- 获取茅台财报: symbol="600519", data_type="fundamental", market="cn"
"""

    def __init__(self):
        """Initialize financial data tool with adapters."""
        self.openbb_adapter = OpenBBAdapter()
        self.akshare_adapter = AkShareAdapter()
        self.compliance = get_compliance_checker()

    def _detect_market(self, symbol: str) -> Market:
        """
        Auto-detect market from symbol format.

        Args:
            symbol: Stock symbol

        Returns:
            Detected market
        """
        symbol = symbol.upper()

        # A-Stock patterns
        if any([
            symbol.endswith(('.SH', '.SS', '.SZ', '.XSHG', '.XSHE')),
            symbol.isdigit() and len(symbol) == 6,
        ]):
            return Market.CN

        # Hong Kong patterns
        if symbol.endswith('.HK') or (symbol.isdigit() and len(symbol) <= 5):
            return Market.HK

        # Default to US
        return Market.US

    def _get_adapter(self, market: Market):
        """
        Get appropriate adapter for market.

        Args:
            market: Target market

        Returns:
            Data adapter instance
        """
        if market == Market.CN:
            if not self.compliance.is_structured_source_enabled("akshare"):
                raise ValueError("AkShare is disabled in compliance config")
            return self.akshare_adapter
        elif market in [Market.US, Market.GLOBAL]:
            if not self.compliance.is_structured_source_enabled("openbb"):
                raise ValueError("OpenBB is disabled in compliance config")
            return self.openbb_adapter
        else:
            # Default to OpenBB for other markets
            return self.openbb_adapter

    async def execute(
        self,
        symbol: str,
        data_type: Literal["quote", "historical", "fundamental", "valuation", "news", "sentiment"] = "quote",
        market: Literal["us", "cn", "hk", "auto"] = "auto",
        **kwargs
    ) -> FinancialDataResult:
        """
        Execute financial data request.

        Args:
            symbol: Stock symbol (e.g., "AAPL", "600519.SH")
            data_type: Type of data to fetch
            market: Target market or "auto" for auto-detection
            **kwargs: Additional arguments passed to adapter

        Returns:
            FinancialDataResult with requested data
        """
        # Auto-detect market if needed
        if market == "auto":
            detected_market = self._detect_market(symbol)
        else:
            detected_market = Market(market)

        # Get appropriate adapter
        try:
            adapter = self._get_adapter(detected_market)
        except ValueError as e:
            return FinancialDataResult(
                success=False,
                error=str(e),
                symbol=symbol,
                market=market,
                data_type=data_type,
            )

        # Route to appropriate method
        try:
            if data_type == "quote":
                return await adapter.get_quote(symbol, **kwargs)
            elif data_type == "historical":
                return await adapter.get_historical(
                    symbol,
                    start_date=kwargs.pop("start_date", None),
                    end_date=kwargs.pop("end_date", None),
                    interval=kwargs.pop("interval", "1d"),
                    **kwargs
                )
            elif data_type == "fundamental":
                return await adapter.get_fundamental(
                    symbol,
                    statement_type=kwargs.get("statement_type", "all"),
                    **kwargs
                )
            elif data_type == "valuation":
                return await adapter.get_valuation(symbol, **kwargs)
            elif data_type == "news":
                return await adapter.get_news(
                    symbol,
                    limit=kwargs.get("limit", 10),
                    **kwargs
                )
            elif data_type == "sentiment":
                # Sentiment requires web crawling - check compliance
                return FinancialDataResult(
                    success=False,
                    error="Sentiment analysis not yet implemented. Use Deep Research with sentiment template.",
                    symbol=symbol,
                    market=detected_market.value,
                    data_type=data_type,
                )
            else:
                return FinancialDataResult(
                    success=False,
                    error=f"Unknown data type: {data_type}",
                    symbol=symbol,
                    market=detected_market.value,
                    data_type=data_type,
                )
        except Exception as e:
            return FinancialDataResult(
                success=False,
                error=str(e),
                source=adapter.name,
                symbol=symbol,
                market=detected_market.value,
                data_type=data_type,
            )

    # Convenience methods

    async def get_quote(self, symbol: str, market: str = "auto", **kwargs) -> FinancialDataResult:
        """Get real-time quote."""
        return await self.execute(symbol, "quote", market, **kwargs)

    async def get_historical(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
        interval: str = "1d",
        market: str = "auto",
        **kwargs
    ) -> FinancialDataResult:
        """Get historical price data."""
        return await self.execute(
            symbol, "historical", market,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            **kwargs
        )

    async def get_fundamental(
        self,
        symbol: str,
        statement_type: str = "all",
        market: str = "auto",
        **kwargs
    ) -> FinancialDataResult:
        """Get financial statements."""
        return await self.execute(
            symbol, "fundamental", market,
            statement_type=statement_type,
            **kwargs
        )

    async def get_valuation(self, symbol: str, market: str = "auto", **kwargs) -> FinancialDataResult:
        """Get valuation metrics."""
        return await self.execute(symbol, "valuation", market, **kwargs)

    async def get_news(
        self,
        symbol: str,
        limit: int = 10,
        market: str = "auto",
        **kwargs
    ) -> FinancialDataResult:
        """Get financial news."""
        return await self.execute(symbol, "news", market, limit=limit, **kwargs)

    # A-Stock specific methods

    async def get_north_flow(self) -> FinancialDataResult:
        """
        Get northbound capital flow (北向资金).

        Returns:
            FinancialDataResult with capital flow data.
        """
        return await self.akshare_adapter.get_north_flow()

    async def get_dragon_tiger(self, date: str | None = None) -> FinancialDataResult:
        """
        Get dragon and tiger list (龙虎榜).

        Args:
            date: Date in YYYYMMDD format

        Returns:
            FinancialDataResult with dragon tiger data.
        """
        return await self.akshare_adapter.get_dragon_tiger(date=date)

    def get_disclaimer(self) -> str:
        """Get compliance disclaimer."""
        return self.compliance.get_disclaimer()


# Singleton instance
_financial_tool: FinancialDataTool | None = None


def get_financial_tool() -> FinancialDataTool:
    """
    Get the global financial data tool instance.

    Returns:
        FinancialDataTool instance
    """
    global _financial_tool

    if _financial_tool is None:
        _financial_tool = FinancialDataTool()

    return _financial_tool
