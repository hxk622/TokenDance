"""
FinancialDataProvider - Multi-source fallback strategy

实现金融数据的多源降级策略：
1. OpenBB (yfinance) → OpenBB (fmp) → 失败
2. AkShare (A股) → 失败
3. 自动检测市场并路由到合适的数据源

使用方法：
    provider = FinancialDataProvider()
    result = await provider.get_data("AAPL", "quote")
"""
import logging
from dataclasses import dataclass
from typing import Any, Literal

from app.agent.tools.builtin.financial.adapters.akshare_adapter import AkShareAdapter
from app.agent.tools.builtin.financial.adapters.base import (
    BaseFinancialAdapter,
    DataType,
    FinancialDataResult,
    Market,
)
from app.agent.tools.builtin.financial.adapters.openbb_adapter import OpenBBAdapter

logger = logging.getLogger(__name__)


@dataclass
class ProviderConfig:
    """数据提供者配置"""
    name: str
    adapter: BaseFinancialAdapter
    priority: int  # 优先级，数字越小优先级越高
    markets: list[Market]  # 支持的市场
    fallback_providers: list[str] = None  # 降级链


class FinancialDataProvider:
    """
    金融数据提供者服务

    实现多源降级策略，自动检测市场并选择最佳数据源。
    当主数据源失败时，自动降级到备用数据源。
    """

    def __init__(self):
        """初始化数据提供者"""
        # 初始化 adapters
        self._openbb_yf = OpenBBAdapter(default_provider="yfinance")
        self._openbb_fmp = OpenBBAdapter(default_provider="fmp")
        self._akshare = AkShareAdapter()

        # 配置提供者优先级
        self._providers: dict[str, ProviderConfig] = {
            "openbb_yfinance": ProviderConfig(
                name="openbb_yfinance",
                adapter=self._openbb_yf,
                priority=1,
                markets=[Market.US, Market.GLOBAL],
                fallback_providers=["openbb_fmp"],
            ),
            "openbb_fmp": ProviderConfig(
                name="openbb_fmp",
                adapter=self._openbb_fmp,
                priority=2,
                markets=[Market.US, Market.GLOBAL],
                fallback_providers=[],
            ),
            "akshare": ProviderConfig(
                name="akshare",
                adapter=self._akshare,
                priority=1,
                markets=[Market.CN],
                fallback_providers=[],  # A股没有备用源
            ),
        }

        # 市场到提供者的映射
        self._market_providers: dict[Market, list[str]] = {
            Market.US: ["openbb_yfinance", "openbb_fmp"],
            Market.GLOBAL: ["openbb_yfinance", "openbb_fmp"],
            Market.CN: ["akshare"],
            Market.HK: ["openbb_yfinance"],  # 港股通过 OpenBB
        }

        logger.info("FinancialDataProvider initialized")

    def _detect_market(self, symbol: str) -> Market:
        """
        根据股票代码自动检测市场

        Args:
            symbol: 股票代码

        Returns:
            检测到的市场
        """
        symbol = symbol.upper()

        # A股模式
        if any([
            symbol.endswith(('.SH', '.SS', '.SZ', '.XSHG', '.XSHE')),
            symbol.isdigit() and len(symbol) == 6,
        ]):
            return Market.CN

        # 港股模式
        if symbol.endswith('.HK') or (symbol.isdigit() and len(symbol) <= 5):
            return Market.HK

        # 默认美股
        return Market.US

    def _get_providers_for_market(self, market: Market) -> list[ProviderConfig]:
        """
        获取指定市场的提供者列表（按优先级排序）

        Args:
            market: 目标市场

        Returns:
            提供者配置列表
        """
        provider_names = self._market_providers.get(market, ["openbb_yfinance"])
        providers = [self._providers[name] for name in provider_names if name in self._providers]
        return sorted(providers, key=lambda p: p.priority)

    async def get_quote(
        self,
        symbol: str,
        market: Literal["auto", "us", "cn", "hk"] = "auto",
        **kwargs
    ) -> FinancialDataResult:
        """
        获取实时行情（带降级策略）

        Args:
            symbol: 股票代码
            market: 市场类型，auto=自动检测
            **kwargs: 额外参数

        Returns:
            行情数据结果
        """
        return await self._get_data_with_fallback(symbol, DataType.QUOTE, market, **kwargs)

    async def get_historical(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
        interval: str = "1d",
        market: Literal["auto", "us", "cn", "hk"] = "auto",
        **kwargs
    ) -> FinancialDataResult:
        """
        获取历史价格（带降级策略）

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            interval: K线周期
            market: 市场类型
            **kwargs: 额外参数

        Returns:
            历史价格数据
        """
        return await self._get_data_with_fallback(
            symbol, DataType.HISTORICAL, market,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            **kwargs
        )

    async def get_fundamental(
        self,
        symbol: str,
        statement_type: str = "all",
        market: Literal["auto", "us", "cn", "hk"] = "auto",
        **kwargs
    ) -> FinancialDataResult:
        """
        获取财务报表（带降级策略）

        Args:
            symbol: 股票代码
            statement_type: 报表类型
            market: 市场类型
            **kwargs: 额外参数

        Returns:
            财务报表数据
        """
        return await self._get_data_with_fallback(
            symbol, DataType.FUNDAMENTAL, market,
            statement_type=statement_type,
            **kwargs
        )

    async def get_valuation(
        self,
        symbol: str,
        market: Literal["auto", "us", "cn", "hk"] = "auto",
        **kwargs
    ) -> FinancialDataResult:
        """
        获取估值指标（带降级策略）

        Args:
            symbol: 股票代码
            market: 市场类型
            **kwargs: 额外参数

        Returns:
            估值指标数据
        """
        return await self._get_data_with_fallback(symbol, DataType.VALUATION, market, **kwargs)

    async def get_news(
        self,
        symbol: str,
        limit: int = 10,
        market: Literal["auto", "us", "cn", "hk"] = "auto",
        **kwargs
    ) -> FinancialDataResult:
        """
        获取财经新闻（带降级策略）

        Args:
            symbol: 股票代码
            limit: 返回数量限制
            market: 市场类型
            **kwargs: 额外参数

        Returns:
            财经新闻数据
        """
        return await self._get_data_with_fallback(
            symbol, DataType.NEWS, market,
            limit=limit,
            **kwargs
        )

    async def _get_data_with_fallback(
        self,
        symbol: str,
        data_type: DataType,
        market: str,
        **kwargs
    ) -> FinancialDataResult:
        """
        带降级策略的数据获取

        尝试按优先级从各数据源获取数据，失败时自动降级。

        Args:
            symbol: 股票代码
            data_type: 数据类型
            market: 市场类型
            **kwargs: 额外参数

        Returns:
            数据结果
        """
        # 检测市场
        if market == "auto":
            detected_market = self._detect_market(symbol)
        else:
            detected_market = Market(market)

        # 获取该市场的提供者列表
        providers = self._get_providers_for_market(detected_market)

        if not providers:
            return FinancialDataResult(
                success=False,
                error=f"No data provider available for market: {detected_market.value}",
                symbol=symbol,
                market=detected_market.value,
                data_type=data_type.value,
            )

        # 记录尝试过的错误
        errors = []

        # 按优先级尝试各提供者
        for provider_config in providers:
            adapter = provider_config.adapter
            provider_name = provider_config.name

            logger.debug(f"Trying provider {provider_name} for {symbol} ({data_type.value})")

            try:
                # 根据数据类型调用对应方法
                if data_type == DataType.QUOTE:
                    result = await adapter.get_quote(symbol, **kwargs)
                elif data_type == DataType.HISTORICAL:
                    result = await adapter.get_historical(symbol, **kwargs)
                elif data_type == DataType.FUNDAMENTAL:
                    result = await adapter.get_fundamental(symbol, **kwargs)
                elif data_type == DataType.VALUATION:
                    result = await adapter.get_valuation(symbol, **kwargs)
                elif data_type == DataType.NEWS:
                    result = await adapter.get_news(symbol, **kwargs)
                else:
                    errors.append(f"{provider_name}: Unsupported data type {data_type}")
                    continue

                # 成功时返回
                if result.success:
                    logger.info(f"Successfully got {data_type.value} for {symbol} from {provider_name}")
                    # 添加提供者信息到 metadata
                    result.metadata["provider_chain"] = provider_name
                    return result
                else:
                    errors.append(f"{provider_name}: {result.error}")
                    logger.warning(f"Provider {provider_name} failed: {result.error}")

            except Exception as e:
                errors.append(f"{provider_name}: {str(e)}")
                logger.error(f"Provider {provider_name} raised exception: {e}")

        # 所有提供者都失败
        return FinancialDataResult(
            success=False,
            error=f"All providers failed. Errors: {'; '.join(errors)}",
            symbol=symbol,
            market=detected_market.value,
            data_type=data_type.value,
            metadata={"attempted_providers": [p.name for p in providers]},
        )

    def get_available_providers(self, market: Market | None = None) -> list[str]:
        """
        获取可用的数据提供者列表

        Args:
            market: 可选的市场过滤

        Returns:
            提供者名称列表
        """
        if market is None:
            return list(self._providers.keys())

        return self._market_providers.get(market, [])

    def get_provider_status(self) -> dict[str, Any]:
        """
        获取所有提供者的状态信息

        Returns:
            提供者状态字典
        """
        return {
            "providers": [
                {
                    "name": config.name,
                    "priority": config.priority,
                    "markets": [m.value for m in config.markets],
                    "fallback_to": config.fallback_providers,
                }
                for config in self._providers.values()
            ],
            "market_mapping": {
                market.value: providers
                for market, providers in self._market_providers.items()
            },
        }


# 单例实例
_provider_instance: FinancialDataProvider | None = None


def get_financial_provider() -> FinancialDataProvider:
    """
    获取金融数据提供者实例（单例）

    Returns:
        FinancialDataProvider 实例
    """
    global _provider_instance

    if _provider_instance is None:
        _provider_instance = FinancialDataProvider()

    return _provider_instance


__all__ = [
    "FinancialDataProvider",
    "ProviderConfig",
    "get_financial_provider",
]
