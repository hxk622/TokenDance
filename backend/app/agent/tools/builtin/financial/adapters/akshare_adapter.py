"""
AkShare adapter for China A-Stock market data.

AkShare is an open-source financial data interface library that provides:
- A-Stock real-time and historical data
- Financial statements for A-Stock companies
- Index data (SSE, SZSE)
- Fund, bond, futures data

Docs: https://akshare.akfamily.xyz
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

# Lazy import to avoid dependency issues
_ak = None


def _get_akshare():
    """Lazy load AkShare."""
    global _ak
    if _ak is None:
        try:
            import akshare as ak
            _ak = ak
        except ImportError:
            raise ImportError(
                "AkShare is not installed. Install with: "
                "uv pip install -e '.[finance]'"
            )
    return _ak


def _normalize_cn_symbol(symbol: str) -> tuple[str, str]:
    """
    Normalize Chinese stock symbol.
    
    Args:
        symbol: Stock symbol (e.g., "600519", "600519.SH", "贵州茅台")
        
    Returns:
        Tuple of (pure_code, market_suffix)
        - pure_code: 6-digit code without suffix
        - market_suffix: "SH" or "SZ"
    """
    # Remove common suffixes
    symbol = symbol.upper()
    for suffix in [".SH", ".SS", ".SZ", ".XSHG", ".XSHE"]:
        if symbol.endswith(suffix):
            symbol = symbol[:-len(suffix)]
            break
    
    # Extract digits
    code = ''.join(filter(str.isdigit, symbol))
    
    if len(code) != 6:
        raise ValueError(f"Invalid A-Stock symbol: {symbol}")
    
    # Determine exchange based on code prefix
    # 60xxxx, 68xxxx -> Shanghai (SH)
    # 00xxxx, 30xxxx -> Shenzhen (SZ)
    if code.startswith(('60', '68', '5')):
        market = "SH"
    elif code.startswith(('00', '30', '1', '2')):
        market = "SZ"
    else:
        market = "SH"  # Default to Shanghai
    
    return code, market


class AkShareAdapter(BaseFinancialAdapter):
    """
    Adapter for AkShare - China A-Stock market data.
    
    Provides access to:
    - Real-time and historical prices
    - Financial statements
    - Market indicators
    - News and announcements
    """
    
    name = "akshare"
    supported_markets = [Market.CN]
    supported_data_types = [
        DataType.QUOTE,
        DataType.HISTORICAL,
        DataType.FUNDAMENTAL,
        DataType.VALUATION,
        DataType.NEWS,
    ]
    
    async def get_quote(self, symbol: str, **kwargs) -> FinancialDataResult:
        """
        Get real-time quote for A-Stock.
        
        Args:
            symbol: Stock symbol (e.g., "600519", "600519.SH")
            
        Returns:
            FinancialDataResult with quote data.
        """
        try:
            code, market = _normalize_cn_symbol(symbol)
            ak = _get_akshare()
            
            loop = asyncio.get_event_loop()
            
            # Get real-time quote using spot data
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_zh_a_spot_em()
            )
            
            # Filter for the specific stock
            row = df[df['代码'] == code]
            
            if row.empty:
                return FinancialDataResult(
                    success=False,
                    error=f"No quote data found for {symbol}",
                    source=self.name,
                    symbol=symbol,
                    market=Market.CN.value,
                    data_type=DataType.QUOTE.value,
                )
            
            # Convert to dict with English keys
            data = row.iloc[0].to_dict()
            
            # Map Chinese keys to English
            key_mapping = {
                '代码': 'code',
                '名称': 'name',
                '最新价': 'price',
                '涨跌幅': 'change_percent',
                '涨跌额': 'change',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '最高': 'high',
                '最低': 'low',
                '今开': 'open',
                '昨收': 'prev_close',
                '量比': 'volume_ratio',
                '换手率': 'turnover_rate',
                '市盈率-动态': 'pe_ttm',
                '市净率': 'pb',
                '总市值': 'market_cap',
                '流通市值': 'float_market_cap',
            }
            
            mapped_data = {}
            for cn_key, en_key in key_mapping.items():
                if cn_key in data:
                    mapped_data[en_key] = data[cn_key]
            
            return FinancialDataResult(
                success=True,
                data=mapped_data,
                source=self.name,
                symbol=f"{code}.{market}",
                market=Market.CN.value,
                data_type=DataType.QUOTE.value,
            )
            
        except Exception as e:
            return FinancialDataResult(
                success=False,
                error=str(e),
                source=self.name,
                symbol=symbol,
                market=Market.CN.value,
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
        Get historical price data for A-Stock.
        
        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD or YYYYMMDD)
            end_date: End date (YYYY-MM-DD or YYYYMMDD)
            interval: Data interval
            
        Returns:
            FinancialDataResult with historical OHLCV data.
        """
        try:
            code, market = _normalize_cn_symbol(symbol)
            ak = _get_akshare()
            
            # Convert date format
            if end_date is None:
                end_date = datetime.now().strftime("%Y%m%d")
            else:
                end_date = end_date.replace("-", "")
                
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
            else:
                start_date = start_date.replace("-", "")
            
            # Map interval
            period_map = {"1d": "daily", "1w": "weekly", "1m": "monthly"}
            period = period_map.get(interval, "daily")
            
            loop = asyncio.get_event_loop()
            
            # Get historical data
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_zh_a_hist(
                    symbol=code,
                    period=period,
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq"  # 前复权 (forward adjusted)
                )
            )
            
            if df.empty:
                return FinancialDataResult(
                    success=False,
                    error=f"No historical data found for {symbol}",
                    source=self.name,
                    symbol=symbol,
                    market=Market.CN.value,
                    data_type=DataType.HISTORICAL.value,
                )
            
            # Rename columns to English
            column_mapping = {
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '涨跌幅': 'change_percent',
                '涨跌额': 'change',
                '换手率': 'turnover_rate',
            }
            
            df = df.rename(columns=column_mapping)
            df['date'] = df['date'].astype(str)
            
            data = df.to_dict(orient='records')
            
            return FinancialDataResult(
                success=True,
                data=data,
                source=self.name,
                symbol=f"{code}.{market}",
                market=Market.CN.value,
                data_type=DataType.HISTORICAL.value,
                metadata={
                    "start_date": start_date,
                    "end_date": end_date,
                    "interval": interval,
                    "records": len(data),
                    "adjust": "qfq",
                },
            )
            
        except Exception as e:
            return FinancialDataResult(
                success=False,
                error=str(e),
                source=self.name,
                symbol=symbol,
                market=Market.CN.value,
                data_type=DataType.HISTORICAL.value,
            )
    
    async def get_fundamental(
        self,
        symbol: str,
        statement_type: Literal["income", "balance", "cashflow", "all"] = "all",
        **kwargs
    ) -> FinancialDataResult:
        """
        Get financial statements for A-Stock.
        
        Args:
            symbol: Stock symbol
            statement_type: Type of statement
            
        Returns:
            FinancialDataResult with financial statement data.
        """
        try:
            code, market = _normalize_cn_symbol(symbol)
            ak = _get_akshare()
            
            loop = asyncio.get_event_loop()
            data: dict[str, Any] = {}
            
            # Fetch income statement
            if statement_type in ["income", "all"]:
                try:
                    df = await loop.run_in_executor(
                        None,
                        lambda: ak.stock_financial_report_sina(
                            stock=code,
                            symbol="利润表"
                        )
                    )
                    if not df.empty:
                        data["income_statement"] = df.head(8).to_dict(orient='records')
                except Exception:
                    pass
            
            # Fetch balance sheet
            if statement_type in ["balance", "all"]:
                try:
                    df = await loop.run_in_executor(
                        None,
                        lambda: ak.stock_financial_report_sina(
                            stock=code,
                            symbol="资产负债表"
                        )
                    )
                    if not df.empty:
                        data["balance_sheet"] = df.head(8).to_dict(orient='records')
                except Exception:
                    pass
            
            # Fetch cash flow statement
            if statement_type in ["cashflow", "all"]:
                try:
                    df = await loop.run_in_executor(
                        None,
                        lambda: ak.stock_financial_report_sina(
                            stock=code,
                            symbol="现金流量表"
                        )
                    )
                    if not df.empty:
                        data["cash_flow"] = df.head(8).to_dict(orient='records')
                except Exception:
                    pass
            
            if not data:
                return FinancialDataResult(
                    success=False,
                    error=f"No fundamental data found for {symbol}",
                    source=self.name,
                    symbol=symbol,
                    market=Market.CN.value,
                    data_type=DataType.FUNDAMENTAL.value,
                )
            
            return FinancialDataResult(
                success=True,
                data=data,
                source=self.name,
                symbol=f"{code}.{market}",
                market=Market.CN.value,
                data_type=DataType.FUNDAMENTAL.value,
                metadata={"statement_type": statement_type},
            )
            
        except Exception as e:
            return FinancialDataResult(
                success=False,
                error=str(e),
                source=self.name,
                symbol=symbol,
                market=Market.CN.value,
                data_type=DataType.FUNDAMENTAL.value,
            )
    
    async def get_valuation(self, symbol: str, **kwargs) -> FinancialDataResult:
        """
        Get valuation metrics for A-Stock.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            FinancialDataResult with valuation metrics.
        """
        try:
            code, market = _normalize_cn_symbol(symbol)
            ak = _get_akshare()
            
            loop = asyncio.get_event_loop()
            
            # Get individual stock metrics
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_a_indicator_lg(symbol=code)
            )
            
            if df.empty:
                return FinancialDataResult(
                    success=False,
                    error=f"No valuation data found for {symbol}",
                    source=self.name,
                    symbol=symbol,
                    market=Market.CN.value,
                    data_type=DataType.VALUATION.value,
                )
            
            # Get the most recent data
            latest = df.iloc[-1].to_dict()
            
            # Rename columns
            column_mapping = {
                'trade_date': 'date',
                'pe': 'pe_ttm',
                'pe_ttm': 'pe_ttm',
                'pb': 'pb',
                'ps': 'ps',
                'ps_ttm': 'ps_ttm',
                'dv_ratio': 'dividend_yield',
                'dv_ttm': 'dividend_yield_ttm',
                'total_mv': 'market_cap',
            }
            
            mapped_data = {}
            for old_key, new_key in column_mapping.items():
                if old_key in latest:
                    mapped_data[new_key] = latest[old_key]
            
            return FinancialDataResult(
                success=True,
                data=mapped_data,
                source=self.name,
                symbol=f"{code}.{market}",
                market=Market.CN.value,
                data_type=DataType.VALUATION.value,
            )
            
        except Exception as e:
            return FinancialDataResult(
                success=False,
                error=str(e),
                source=self.name,
                symbol=symbol,
                market=Market.CN.value,
                data_type=DataType.VALUATION.value,
            )
    
    async def get_news(self, symbol: str, limit: int = 10, **kwargs) -> FinancialDataResult:
        """
        Get news for A-Stock company.
        
        Args:
            symbol: Stock symbol
            limit: Maximum number of news items
            
        Returns:
            FinancialDataResult with news data.
        """
        try:
            code, market = _normalize_cn_symbol(symbol)
            ak = _get_akshare()
            
            loop = asyncio.get_event_loop()
            
            # Get company announcements from East Money
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_notice_report(symbol=code)
            )
            
            if df.empty:
                return FinancialDataResult(
                    success=False,
                    error=f"No news found for {symbol}",
                    source=self.name,
                    symbol=symbol,
                    market=Market.CN.value,
                    data_type=DataType.NEWS.value,
                )
            
            # Limit results
            df = df.head(limit)
            
            data = df.to_dict(orient='records')
            
            return FinancialDataResult(
                success=True,
                data=data,
                source=self.name,
                symbol=f"{code}.{market}",
                market=Market.CN.value,
                data_type=DataType.NEWS.value,
                metadata={"count": len(data)},
            )
            
        except Exception as e:
            return FinancialDataResult(
                success=False,
                error=str(e),
                source=self.name,
                symbol=symbol,
                market=Market.CN.value,
                data_type=DataType.NEWS.value,
            )
    
    # Additional A-Stock specific methods
    
    async def get_north_flow(self, **kwargs) -> FinancialDataResult:
        """
        Get northbound capital flow (沪深港通北向资金).
        
        Returns:
            FinancialDataResult with capital flow data.
        """
        try:
            ak = _get_akshare()
            loop = asyncio.get_event_loop()
            
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_hsgt_north_net_flow_in_em()
            )
            
            if df.empty:
                return FinancialDataResult(
                    success=False,
                    error="No north flow data found",
                    source=self.name,
                    symbol="",
                    market=Market.CN.value,
                    data_type="north_flow",
                )
            
            data = df.to_dict(orient='records')
            
            return FinancialDataResult(
                success=True,
                data=data,
                source=self.name,
                symbol="",
                market=Market.CN.value,
                data_type="north_flow",
            )
            
        except Exception as e:
            return FinancialDataResult(
                success=False,
                error=str(e),
                source=self.name,
                symbol="",
                market=Market.CN.value,
                data_type="north_flow",
            )
    
    async def get_dragon_tiger(
        self,
        date: str | None = None,
        **kwargs
    ) -> FinancialDataResult:
        """
        Get dragon and tiger list (龙虎榜).
        
        Args:
            date: Date in YYYYMMDD format. Default: latest trading day.
            
        Returns:
            FinancialDataResult with dragon tiger data.
        """
        try:
            ak = _get_akshare()
            loop = asyncio.get_event_loop()
            
            if date is None:
                date = datetime.now().strftime("%Y%m%d")
            
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_lhb_detail_em(
                    start_date=date,
                    end_date=date
                )
            )
            
            if df.empty:
                return FinancialDataResult(
                    success=False,
                    error=f"No dragon tiger data found for {date}",
                    source=self.name,
                    symbol="",
                    market=Market.CN.value,
                    data_type="dragon_tiger",
                )
            
            data = df.to_dict(orient='records')
            
            return FinancialDataResult(
                success=True,
                data=data,
                source=self.name,
                symbol="",
                market=Market.CN.value,
                data_type="dragon_tiger",
                metadata={"date": date},
            )
            
        except Exception as e:
            return FinancialDataResult(
                success=False,
                error=str(e),
                source=self.name,
                symbol="",
                market=Market.CN.value,
                data_type="dragon_tiger",
            )
