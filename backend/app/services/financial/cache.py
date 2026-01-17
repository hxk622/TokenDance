"""
金融分析缓存服务

提供：
1. 分析结果缓存 (Redis)
2. 并行分析执行
3. 缓存失效策略

使用方法：
    from app.services.financial.cache import AnalysisCache, run_parallel_analysis

    # 使用缓存
    cache = AnalysisCache()
    result = await cache.get_or_analyze("AAPL", "financial")

    # 并行分析
    results = await run_parallel_analysis("AAPL", "us")
"""
import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

# 缓存 TTL 配置 (秒)
CACHE_TTL = {
    "quote": 60,              # 报价：1分钟
    "financial": 3600,        # 财务分析：1小时
    "valuation": 1800,        # 估值分析：30分钟
    "technical": 300,         # 技术分析：5分钟
    "comprehensive": 300,     # 综合分析：5分钟
    "historical": 86400,      # 历史数据：1天
    "fundamental": 86400,     # 基本面：1天
}

T = TypeVar('T')


class AnalysisCache:
    """
    金融分析缓存服务

    支持 Redis 缓存（可选）和本地内存缓存。
    """

    def __init__(self):
        """初始化缓存服务"""
        self._redis_client = None
        self._local_cache: dict[str, tuple[Any, datetime]] = {}
        self._redis_available = False

    async def _get_redis(self):
        """获取 Redis 客户端"""
        if self._redis_client is None:
            try:
                from app.core.redis import get_redis_client
                self._redis_client = await get_redis_client()
                self._redis_available = self._redis_client is not None
            except Exception as e:
                logger.debug(f"Redis not available: {e}")
                self._redis_available = False
        return self._redis_client if self._redis_available else None

    def _make_key(self, symbol: str, analysis_type: str, market: str = "") -> str:
        """生成缓存键"""
        key_str = f"financial:{analysis_type}:{symbol}:{market}"
        return hashlib.md5(key_str.encode()).hexdigest()[:16]

    async def get(
        self,
        symbol: str,
        analysis_type: str,
        market: str = ""
    ) -> dict[str, Any] | None:
        """
        获取缓存的分析结果

        Args:
            symbol: 股票代码
            analysis_type: 分析类型 (financial/valuation/technical)
            market: 市场

        Returns:
            缓存的结果，如果不存在或过期返回 None
        """
        key = self._make_key(symbol, analysis_type, market)

        # 尝试 Redis
        redis = await self._get_redis()
        if redis:
            try:
                cached = await redis.get(f"analysis:{key}")
                if cached:
                    logger.debug(f"Cache hit (Redis): {key}")
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Redis get error: {e}")

        # 回退到本地缓存
        if key in self._local_cache:
            data, timestamp = self._local_cache[key]
            ttl = CACHE_TTL.get(analysis_type, 300)
            if datetime.now() - timestamp < timedelta(seconds=ttl):
                logger.debug(f"Cache hit (local): {key}")
                return data
            else:
                # 过期，删除
                del self._local_cache[key]

        return None

    async def set(
        self,
        symbol: str,
        analysis_type: str,
        data: dict[str, Any],
        market: str = ""
    ) -> None:
        """
        缓存分析结果

        Args:
            symbol: 股票代码
            analysis_type: 分析类型
            data: 要缓存的数据
            market: 市场
        """
        key = self._make_key(symbol, analysis_type, market)
        ttl = CACHE_TTL.get(analysis_type, 300)

        # 尝试 Redis
        redis = await self._get_redis()
        if redis:
            try:
                await redis.setex(
                    f"analysis:{key}",
                    ttl,
                    json.dumps(data, ensure_ascii=False, default=str)
                )
                logger.debug(f"Cache set (Redis): {key}, TTL={ttl}s")
            except Exception as e:
                logger.warning(f"Redis set error: {e}")

        # 同时写入本地缓存
        self._local_cache[key] = (data, datetime.now())
        logger.debug(f"Cache set (local): {key}")

    async def invalidate(
        self,
        symbol: str,
        analysis_type: str | None = None,
        market: str = ""
    ) -> None:
        """
        使缓存失效

        Args:
            symbol: 股票代码
            analysis_type: 分析类型，如果为 None 则清除该股票所有缓存
            market: 市场
        """
        types_to_clear = [analysis_type] if analysis_type else list(CACHE_TTL.keys())

        for atype in types_to_clear:
            key = self._make_key(symbol, atype, market)

            # Redis
            redis = await self._get_redis()
            if redis:
                try:
                    await redis.delete(f"analysis:{key}")
                except Exception:
                    pass

            # 本地缓存
            if key in self._local_cache:
                del self._local_cache[key]

        logger.info(f"Cache invalidated: {symbol}, types={types_to_clear}")

    def clear_local(self) -> None:
        """清除本地缓存"""
        self._local_cache.clear()
        logger.info("Local cache cleared")


# 全局缓存实例
_cache_instance: AnalysisCache | None = None


def get_analysis_cache() -> AnalysisCache:
    """获取缓存单例"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = AnalysisCache()
    return _cache_instance


async def run_parallel_analysis(
    symbol: str,
    market: str = "auto",
    include_technical: bool = True,
    use_cache: bool = True,
) -> dict[str, Any]:
    """
    并行运行所有分析

    相比顺序执行，可以将总耗时从 T1+T2+T3 优化为 max(T1, T2, T3)。

    Args:
        symbol: 股票代码
        market: 市场
        include_technical: 是否包含技术分析
        use_cache: 是否使用缓存

    Returns:
        综合分析结果
    """
    from app.services.financial import (
        get_financial_analyzer,
        get_technical_indicators,
        get_valuation_analyzer,
    )

    cache = get_analysis_cache() if use_cache else None

    results = {
        "symbol": symbol,
        "market": market,
        "financial": None,
        "valuation": None,
        "technical": None,
        "summary": "",
        "generated_at": datetime.now().isoformat(),
        "cache_hits": [],
    }

    async def run_financial():
        """运行财务分析"""
        # 检查缓存
        if cache:
            cached = await cache.get(symbol, "financial", market)
            if cached:
                results["cache_hits"].append("financial")
                return cached

        try:
            analyzer = get_financial_analyzer()
            result = await analyzer.analyze(symbol, market)
            data = result.to_dict()

            # 写入缓存
            if cache:
                await cache.set(symbol, "financial", data, market)

            return data
        except Exception as e:
            logger.error(f"Financial analysis failed: {e}")
            return {"error": str(e)}

    async def run_valuation():
        """运行估值分析"""
        if cache:
            cached = await cache.get(symbol, "valuation", market)
            if cached:
                results["cache_hits"].append("valuation")
                return cached

        try:
            analyzer = get_valuation_analyzer()
            result = await analyzer.analyze(symbol, market)
            data = result.to_dict()

            if cache:
                await cache.set(symbol, "valuation", data, market)

            return data
        except Exception as e:
            logger.error(f"Valuation analysis failed: {e}")
            return {"error": str(e)}

    async def run_technical():
        """运行技术分析"""
        if cache:
            cached = await cache.get(symbol, "technical", market)
            if cached:
                results["cache_hits"].append("technical")
                return cached

        try:
            service = get_technical_indicators()
            result = await service.analyze(symbol, market)
            data = result.to_dict()

            if cache:
                await cache.set(symbol, "technical", data, market)

            return data
        except Exception as e:
            logger.error(f"Technical analysis failed: {e}")
            return {"error": str(e)}

    # 并行执行
    tasks = [run_financial(), run_valuation()]
    if include_technical:
        tasks.append(run_technical())

    start_time = datetime.now()

    # 使用 gather 并行执行
    analysis_results = await asyncio.gather(*tasks, return_exceptions=True)

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"Parallel analysis completed in {elapsed:.2f}s, cache_hits={results['cache_hits']}")

    # 处理结果
    results["financial"] = analysis_results[0] if not isinstance(analysis_results[0], Exception) else {"error": str(analysis_results[0])}
    results["valuation"] = analysis_results[1] if not isinstance(analysis_results[1], Exception) else {"error": str(analysis_results[1])}

    if include_technical and len(analysis_results) > 2:
        results["technical"] = analysis_results[2] if not isinstance(analysis_results[2], Exception) else {"error": str(analysis_results[2])}

    # 生成综合摘要
    summaries = []
    for key in ["financial", "valuation", "technical"]:
        if results.get(key) and not results[key].get("error"):
            summary = results[key].get("summary", "")
            if summary:
                summaries.append(summary)

    results["summary"] = " ".join(summaries)
    results["elapsed_seconds"] = elapsed

    return results


async def benchmark_analysis(
    symbol: str,
    market: str = "us",
    iterations: int = 3,
) -> dict[str, Any]:
    """
    分析性能基准测试

    Args:
        symbol: 测试股票代码
        market: 市场
        iterations: 测试迭代次数

    Returns:
        性能测试结果
    """
    import time

    results = {
        "symbol": symbol,
        "market": market,
        "iterations": iterations,
        "sequential": {"times": [], "avg": 0},
        "parallel": {"times": [], "avg": 0},
        "parallel_cached": {"times": [], "avg": 0},
        "speedup": 0,
    }

    from app.services.financial import (
        get_financial_analyzer,
        get_technical_indicators,
        get_valuation_analyzer,
    )

    # 顺序执行测试
    for _ in range(iterations):
        start = time.time()

        try:
            await get_financial_analyzer().analyze(symbol, market)
            await get_valuation_analyzer().analyze(symbol, market)
            await get_technical_indicators().analyze(symbol, market)
        except Exception:
            pass

        elapsed = time.time() - start
        results["sequential"]["times"].append(elapsed)

    results["sequential"]["avg"] = sum(results["sequential"]["times"]) / iterations

    # 清除缓存
    cache = get_analysis_cache()
    await cache.invalidate(symbol)

    # 并行执行测试（无缓存）
    for _ in range(iterations):
        start = time.time()
        await run_parallel_analysis(symbol, market, use_cache=False)
        elapsed = time.time() - start
        results["parallel"]["times"].append(elapsed)

    results["parallel"]["avg"] = sum(results["parallel"]["times"]) / iterations

    # 并行执行测试（有缓存，第一次填充缓存）
    await cache.invalidate(symbol)
    for _i in range(iterations):
        start = time.time()
        await run_parallel_analysis(symbol, market, use_cache=True)
        elapsed = time.time() - start
        results["parallel_cached"]["times"].append(elapsed)

    results["parallel_cached"]["avg"] = sum(results["parallel_cached"]["times"]) / iterations

    # 计算加速比
    if results["parallel"]["avg"] > 0:
        results["speedup"] = results["sequential"]["avg"] / results["parallel"]["avg"]

    return results
