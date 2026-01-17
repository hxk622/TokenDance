"""
OpenBB adapter for global financial data.

OpenBB Platform provides access to 100+ data sources for:
- US stocks, ETFs, indices
- Global equities
- Macro economic data
- Options, futures, forex, crypto

Docs: https://docs.openbb.co
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Literal

from app.agent.tools.builtin.financial.adapters.base import (
    BaseFinancialAdapter,
    DataType,
    FinancialDataResult,
    Market,
)

# Lazy import to avoid dependency issues when openbb is not installed
_obb = None


def _get_obb():
    """Lazy load OpenBB SDK."""
    global _obb
    if _obb is None:
        try:
            from openbb import obb
            _obb = obb
        except ImportError:
            raise ImportError(
                "OpenBB is not installed. Install with: "
                "uv pip install -e '.[finance]'"
            )
    return _obb


class OpenBBAdapter(BaseFinancialAdapter):
    """
    Adapter for OpenBB Platform.

    Provides access to global financial data through a unified interface.
    Supports multiple data providers (Yahoo Finance, FMP, FRED, etc.).
    """

    name = "openbb"
    supported_markets = [Market.US, Market.GLOBAL]
    supported_data_types = [
        DataType.QUOTE,
        DataType.HISTORICAL,
        DataType.FUNDAMENTAL,
        DataType.VALUATION,
        DataType.NEWS,
        DataType.ANALYST,
    ]

    def __init__(self, default_provider: str = "yfinance"):
        """
        Initialize OpenBB adapter.

        Args:
            default_provider: Default data provider. Options:
                - yfinance: Yahoo Finance (free, no API key)
                - fmp: Financial Modeling Prep (API key required)
                - polygon: Polygon.io (API key required)
                - intrinio: Intrinio (API key required)
        """
        self.default_provider = default_provider

    async def get_quote(self, symbol: str, **kwargs) -> FinancialDataResult:
        """
        Get real-time or delayed quote.

        Args:
            symbol: Stock symbol (e.g., "AAPL", "MSFT")
            **kwargs: Additional arguments (provider, etc.)

        Returns:
            FinancialDataResult with quote data.
        """
        provider = kwargs.get("provider", self.default_provider)

        try:
            obb = _get_obb()

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: obb.equity.price.quote(symbol, provider=provider)
            )

            # Convert to dataframe and then to dict
            df = result.to_dataframe()

            if df.empty:
                return FinancialDataResult(
                    success=False,
                    error=f"No quote data found for {symbol}",
                    source=self.name,
                    symbol=symbol,
                    market=Market.US.value,
                    data_type=DataType.QUOTE.value,
                )

            # Get the first row as dict
            data = df.iloc[0].to_dict()

            # Clean NaN values
            data = {k: (None if str(v) == 'nan' else v) for k, v in data.items()}

            return FinancialDataResult(
                success=True,
                data=data,
                source=self.name,
                symbol=symbol,
                market=Market.US.value,
                data_type=DataType.QUOTE.value,
                metadata={"provider": provider},
            )

        except Exception as e:
            return FinancialDataResult(
                success=False,
                error=str(e),
                source=self.name,
                symbol=symbol,
                market=Market.US.value,
                data_type=DataType.QUOTE.value,
            )

    async def get_historical(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
        interval: Literal["1d", "1w", "1m"] = "1d",
        **kwargs
    ) -> FinancialDataResult:
        """
        Get historical price data.

        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD). Default: 1 year ago
            end_date: End date (YYYY-MM-DD). Default: today
            interval: Data interval (1d=daily, 1w=weekly, 1m=monthly)

        Returns:
            FinancialDataResult with historical OHLCV data.
        """
        provider = kwargs.get("provider", self.default_provider)

        # Default date range: 1 year
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        try:
            obb = _get_obb()

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: obb.equity.price.historical(
                    symbol,
                    start_date=start_date,
                    end_date=end_date,
                    provider=provider,
                )
            )

            df = result.to_dataframe()

            if df.empty:
                return FinancialDataResult(
                    success=False,
                    error=f"No historical data found for {symbol}",
                    source=self.name,
                    symbol=symbol,
                    market=Market.US.value,
                    data_type=DataType.HISTORICAL.value,
                )

            # Convert dataframe to list of dicts
            # Reset index to get date as column
            df = df.reset_index()
            if 'date' in df.columns:
                df['date'] = df['date'].astype(str)

            data = df.to_dict(orient='records')

            return FinancialDataResult(
                success=True,
                data=data,
                source=self.name,
                symbol=symbol,
                market=Market.US.value,
                data_type=DataType.HISTORICAL.value,
                metadata={
                    "provider": provider,
                    "start_date": start_date,
                    "end_date": end_date,
                    "interval": interval,
                    "records": len(data),
                },
            )

        except Exception as e:
            return FinancialDataResult(
                success=False,
                error=str(e),
                source=self.name,
                symbol=symbol,
                market=Market.US.value,
                data_type=DataType.HISTORICAL.value,
            )

    async def get_fundamental(
        self,
        symbol: str,
        statement_type: Literal["income", "balance", "cashflow", "all"] = "all",
        **kwargs
    ) -> FinancialDataResult:
        """
        Get financial statements.

        Args:
            symbol: Stock symbol
            statement_type: Type of statement to fetch

        Returns:
            FinancialDataResult with financial statement data.
        """
        provider = kwargs.get("provider", "fmp")  # FMP has better fundamental data
        period = kwargs.get("period", "annual")  # annual or quarterly
        limit = kwargs.get("limit", 5)

        try:
            obb = _get_obb()
            loop = asyncio.get_event_loop()

            data: dict[str, Any] = {}

            # Fetch requested statements
            if statement_type in ["income", "all"]:
                result = await loop.run_in_executor(
                    None,
                    lambda: obb.equity.fundamental.income(
                        symbol, period=period, limit=limit, provider=provider
                    )
                )
                df = result.to_dataframe()
                if not df.empty:
                    data["income_statement"] = df.to_dict(orient='records')

            if statement_type in ["balance", "all"]:
                result = await loop.run_in_executor(
                    None,
                    lambda: obb.equity.fundamental.balance(
                        symbol, period=period, limit=limit, provider=provider
                    )
                )
                df = result.to_dataframe()
                if not df.empty:
                    data["balance_sheet"] = df.to_dict(orient='records')

            if statement_type in ["cashflow", "all"]:
                result = await loop.run_in_executor(
                    None,
                    lambda: obb.equity.fundamental.cash(
                        symbol, period=period, limit=limit, provider=provider
                    )
                )
                df = result.to_dataframe()
                if not df.empty:
                    data["cash_flow"] = df.to_dict(orient='records')

            if not data:
                return FinancialDataResult(
                    success=False,
                    error=f"No fundamental data found for {symbol}",
                    source=self.name,
                    symbol=symbol,
                    market=Market.US.value,
                    data_type=DataType.FUNDAMENTAL.value,
                )

            return FinancialDataResult(
                success=True,
                data=data,
                source=self.name,
                symbol=symbol,
                market=Market.US.value,
                data_type=DataType.FUNDAMENTAL.value,
                metadata={
                    "provider": provider,
                    "period": period,
                    "statement_type": statement_type,
                },
            )

        except Exception as e:
            return FinancialDataResult(
                success=False,
                error=str(e),
                source=self.name,
                symbol=symbol,
                market=Market.US.value,
                data_type=DataType.FUNDAMENTAL.value,
            )

    async def get_valuation(self, symbol: str, **kwargs) -> FinancialDataResult:
        """
        Get valuation metrics (PE, PB, PS, etc.).

        Args:
            symbol: Stock symbol

        Returns:
            FinancialDataResult with valuation metrics.
        """
        provider = kwargs.get("provider", "fmp")

        try:
            obb = _get_obb()
            loop = asyncio.get_event_loop()

            # Get key metrics
            result = await loop.run_in_executor(
                None,
                lambda: obb.equity.fundamental.metrics(symbol, provider=provider)
            )

            df = result.to_dataframe()

            if df.empty:
                return FinancialDataResult(
                    success=False,
                    error=f"No valuation data found for {symbol}",
                    source=self.name,
                    symbol=symbol,
                    market=Market.US.value,
                    data_type=DataType.VALUATION.value,
                )

            # Get the most recent metrics
            data = df.iloc[0].to_dict()

            # Clean NaN values
            data = {k: (None if str(v) == 'nan' else v) for k, v in data.items()}

            return FinancialDataResult(
                success=True,
                data=data,
                source=self.name,
                symbol=symbol,
                market=Market.US.value,
                data_type=DataType.VALUATION.value,
                metadata={"provider": provider},
            )

        except Exception as e:
            return FinancialDataResult(
                success=False,
                error=str(e),
                source=self.name,
                symbol=symbol,
                market=Market.US.value,
                data_type=DataType.VALUATION.value,
            )

    async def get_news(self, symbol: str, limit: int = 10, **kwargs) -> FinancialDataResult:
        """
        Get financial news for a symbol.

        Args:
            symbol: Stock symbol
            limit: Maximum number of news items

        Returns:
            FinancialDataResult with news data.
        """
        provider = kwargs.get("provider", "fmp")

        try:
            obb = _get_obb()
            loop = asyncio.get_event_loop()

            result = await loop.run_in_executor(
                None,
                lambda: obb.news.company(symbol, limit=limit, provider=provider)
            )

            df = result.to_dataframe()

            if df.empty:
                return FinancialDataResult(
                    success=False,
                    error=f"No news found for {symbol}",
                    source=self.name,
                    symbol=symbol,
                    market=Market.US.value,
                    data_type=DataType.NEWS.value,
                )

            data = df.to_dict(orient='records')

            return FinancialDataResult(
                success=True,
                data=data,
                source=self.name,
                symbol=symbol,
                market=Market.US.value,
                data_type=DataType.NEWS.value,
                metadata={"provider": provider, "count": len(data)},
            )

        except Exception as e:
            return FinancialDataResult(
                success=False,
                error=str(e),
                source=self.name,
                symbol=symbol,
                market=Market.US.value,
                data_type=DataType.NEWS.value,
            )

    async def get_analyst_ratings(self, symbol: str, **kwargs) -> FinancialDataResult:
        """
        Get analyst ratings and price targets.

        Args:
            symbol: Stock symbol

        Returns:
            FinancialDataResult with analyst data.
        """
        provider = kwargs.get("provider", "fmp")

        try:
            obb = _get_obb()
            loop = asyncio.get_event_loop()

            # Get analyst estimates
            result = await loop.run_in_executor(
                None,
                lambda: obb.equity.estimates.consensus(symbol, provider=provider)
            )

            df = result.to_dataframe()

            if df.empty:
                return FinancialDataResult(
                    success=False,
                    error=f"No analyst data found for {symbol}",
                    source=self.name,
                    symbol=symbol,
                    market=Market.US.value,
                    data_type=DataType.ANALYST.value,
                )

            data = df.to_dict(orient='records')

            return FinancialDataResult(
                success=True,
                data=data,
                source=self.name,
                symbol=symbol,
                market=Market.US.value,
                data_type=DataType.ANALYST.value,
                metadata={"provider": provider},
            )

        except Exception as e:
            return FinancialDataResult(
                success=False,
                error=str(e),
                source=self.name,
                symbol=symbol,
                market=Market.US.value,
                data_type=DataType.ANALYST.value,
            )
