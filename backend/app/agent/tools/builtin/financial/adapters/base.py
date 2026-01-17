"""Base class for financial data adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal


class DataType(str, Enum):
    """Types of financial data."""
    QUOTE = "quote"                    # Real-time/delayed quote
    HISTORICAL = "historical"          # Historical prices
    FUNDAMENTAL = "fundamental"        # Financial statements
    VALUATION = "valuation"            # Valuation metrics (PE, PB, etc.)
    NEWS = "news"                      # Financial news
    SENTIMENT = "sentiment"            # Market sentiment
    HOLDINGS = "holdings"              # Institutional holdings
    ANALYST = "analyst"                # Analyst ratings


class Market(str, Enum):
    """Supported markets."""
    US = "us"          # US Stock (NYSE, NASDAQ)
    CN = "cn"          # China A-Stock (SSE, SZSE)
    HK = "hk"          # Hong Kong (HKEX)
    GLOBAL = "global"  # Global markets


@dataclass
class FinancialDataResult:
    """Standard result format for financial data."""

    success: bool
    data: dict[str, Any] | list[dict[str, Any]] | None = None
    error: str | None = None
    source: str = ""
    symbol: str = ""
    market: str = ""
    data_type: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "source": self.source,
            "symbol": self.symbol,
            "market": self.market,
            "data_type": self.data_type,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class BaseFinancialAdapter(ABC):
    """Base class for financial data adapters."""

    name: str = "base"
    supported_markets: list[Market] = []
    supported_data_types: list[DataType] = []

    @abstractmethod
    async def get_quote(self, symbol: str, **kwargs) -> FinancialDataResult:
        """Get real-time or delayed quote."""
        pass

    @abstractmethod
    async def get_historical(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
        interval: Literal["1d", "1w", "1m"] = "1d",
        **kwargs
    ) -> FinancialDataResult:
        """Get historical price data."""
        pass

    @abstractmethod
    async def get_fundamental(
        self,
        symbol: str,
        statement_type: Literal["income", "balance", "cashflow", "all"] = "all",
        **kwargs
    ) -> FinancialDataResult:
        """Get financial statements."""
        pass

    @abstractmethod
    async def get_valuation(self, symbol: str, **kwargs) -> FinancialDataResult:
        """Get valuation metrics."""
        pass

    async def get_news(self, symbol: str, limit: int = 10, **kwargs) -> FinancialDataResult:
        """Get financial news. Optional, may not be supported by all adapters."""
        return FinancialDataResult(
            success=False,
            error=f"News not supported by {self.name}",
            source=self.name,
            symbol=symbol,
            data_type=DataType.NEWS.value,
        )

    async def get_analyst_ratings(self, symbol: str, **kwargs) -> FinancialDataResult:
        """Get analyst ratings. Optional, may not be supported by all adapters."""
        return FinancialDataResult(
            success=False,
            error=f"Analyst ratings not supported by {self.name}",
            source=self.name,
            symbol=symbol,
            data_type=DataType.ANALYST.value,
        )

    def supports_market(self, market: Market) -> bool:
        """Check if adapter supports the given market."""
        return market in self.supported_markets

    def supports_data_type(self, data_type: DataType) -> bool:
        """Check if adapter supports the given data type."""
        return data_type in self.supported_data_types
