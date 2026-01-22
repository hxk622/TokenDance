"""
Unit tests for IndustryBenchmarkService.

Run with:
    cd backend && uv run pytest tests/services/financial/test_benchmark.py -v
"""

import pytest

from app.services.financial.benchmark.industry_benchmark import (
    DuPontDecomposition,
    DuPontFactor,
    IndustryBenchmark,
    IndustryBenchmarkService,
    TrendDirection,
)


class TestIndustryBenchmarkService:
    """Tests for IndustryBenchmarkService."""

    @pytest.fixture
    def service(self) -> IndustryBenchmarkService:
        """Create service instance."""
        return IndustryBenchmarkService()

    @pytest.mark.asyncio
    async def test_get_percentile_basic(self, service: IndustryBenchmarkService):
        """Test basic percentile calculation."""
        result = await service.get_percentile(
            symbol="600519",
            metric="roe",
        )

        assert isinstance(result, IndustryBenchmark)
        assert result.metric_key == "roe"
        assert 0 <= result.percentile <= 100
        assert result.current_value is not None
        assert result.percentile_50 is not None  # median
        assert result.percentile_75 is not None  # top quartile

    @pytest.mark.asyncio
    async def test_get_dupont_decomposition(self, service: IndustryBenchmarkService):
        """Test DuPont decomposition for ROE."""
        result = await service.get_dupont_decomposition(
            symbol="600519",
        )

        assert isinstance(result, DuPontDecomposition)
        assert result.symbol == "600519"
        assert result.roe is not None

        # Check three factors
        assert result.net_profit_margin is not None
        assert result.asset_turnover is not None
        assert result.equity_multiplier is not None

        # Check factor structure
        assert isinstance(result.net_profit_margin, DuPontFactor)
        assert result.net_profit_margin.value is not None
        assert 0 <= result.net_profit_margin.percentile <= 100

    @pytest.mark.asyncio
    async def test_get_percentile_non_roe(
        self, service: IndustryBenchmarkService
    ):
        """Test percentile for non-ROE metrics."""
        result = await service.get_percentile(
            symbol="600519",
            metric="gross_margin",
        )

        assert result.metric_key == "gross_margin"
        assert 0 <= result.percentile <= 100

    @pytest.mark.asyncio
    async def test_get_multiple_percentiles(self, service: IndustryBenchmarkService):
        """Test getting multiple metrics at once."""
        metrics = ["roe", "gross_margin", "debt_ratio"]
        results = await service.get_multiple_percentiles(
            symbol="600519",
            metrics=metrics,
        )

        assert len(results) == 3
        result_metrics = [r.metric_key for r in results]
        for metric in metrics:
            assert metric in result_metrics

    @pytest.mark.asyncio
    async def test_percentile_value_ranges(self, service: IndustryBenchmarkService):
        """Test that percentile values are within valid ranges."""
        result = await service.get_percentile(
            symbol="600519",
            metric="roe",
        )

        # Percentile should be between 0 and 100
        assert 0 <= result.percentile <= 100

        # Quartile values should follow: P25 < P50 < P75
        if all([
            result.percentile_25,
            result.percentile_50,
            result.percentile_75
        ]):
            assert result.percentile_25 <= result.percentile_50
            assert result.percentile_50 <= result.percentile_75

    @pytest.mark.asyncio
    async def test_dupont_factor_structure(self, service: IndustryBenchmarkService):
        """Test DuPont factor data structure."""
        result = await service.get_dupont_decomposition(
            symbol="600519",
        )

        # Check net profit margin factor
        factor = result.net_profit_margin
        assert isinstance(factor, DuPontFactor)
        assert factor.name is not None
        assert factor.value is not None
        assert 0 <= factor.percentile <= 100
        assert factor.trend in TrendDirection

    @pytest.mark.asyncio
    async def test_different_symbols(self, service: IndustryBenchmarkService):
        """Test with different stock symbols."""
        symbols = ["600519", "000858", "601318"]

        for symbol in symbols:
            result = await service.get_percentile(
                symbol=symbol,
                metric="roe",
            )

            assert result.percentile is not None
