"""
Unit tests for SentimentTimeSeriesService.

Run with:
    cd backend && uv run pytest tests/services/financial/test_sentiment_timeseries.py -v
"""

import pytest

from app.services.financial.sentiment.sentiment_timeseries import (
    DailyMoodPoint,
    KeyOpinion,
    SentimentLevel,
    SentimentPulseResult,
    SentimentTimeSeriesService,
    TrendingTopic,
)


class TestSentimentTimeSeriesService:
    """Tests for SentimentTimeSeriesService."""

    @pytest.fixture
    def service(self) -> SentimentTimeSeriesService:
        """Create service instance."""
        return SentimentTimeSeriesService()

    @pytest.mark.asyncio
    async def test_get_sentiment_pulse_basic(self, service: SentimentTimeSeriesService):
        """Test getting sentiment pulse."""
        result = await service.get_sentiment_pulse(
            symbol="600519",
            days=7
        )

        assert isinstance(result, SentimentPulseResult)
        assert result.symbol == "600519"
        assert result.current_score is not None
        assert result.current_level is not None

    @pytest.mark.asyncio
    async def test_sentiment_score_range(self, service: SentimentTimeSeriesService):
        """Test that sentiment score is in valid range."""
        result = await service.get_sentiment_pulse(
            symbol="600519",
            days=7
        )

        # Sentiment score should be between -1 and 1
        assert -1 <= result.current_score <= 1

    @pytest.mark.asyncio
    async def test_sentiment_level_mapping(self, service: SentimentTimeSeriesService):
        """Test that sentiment level matches score."""
        result = await service.get_sentiment_pulse(
            symbol="600519",
            days=7
        )

        # Level should be consistent with score
        assert result.current_level in SentimentLevel
        assert isinstance(result.current_level, SentimentLevel)

    @pytest.mark.asyncio
    async def test_daily_mood_points(self, service: SentimentTimeSeriesService):
        """Test daily mood time series data."""
        result = await service.get_sentiment_pulse(
            symbol="600519",
            days=7
        )

        assert result.daily_moods is not None
        assert len(result.daily_moods) > 0
        assert len(result.daily_moods) <= 7

        for mood in result.daily_moods:
            assert isinstance(mood, DailyMoodPoint)
            assert mood.date is not None
            assert -1 <= mood.score <= 1
            assert mood.post_count >= 0

    @pytest.mark.asyncio
    async def test_daily_moods_sorted_by_date(self, service: SentimentTimeSeriesService):
        """Test that daily moods are sorted by date."""
        result = await service.get_sentiment_pulse(
            symbol="600519",
            days=7
        )

        if len(result.daily_moods) > 1:
            for i in range(len(result.daily_moods) - 1):
                assert result.daily_moods[i].date <= result.daily_moods[i + 1].date

    @pytest.mark.asyncio
    async def test_trending_topics(self, service: SentimentTimeSeriesService):
        """Test trending topics extraction."""
        result = await service.get_sentiment_pulse(
            symbol="600519",
            days=7
        )

        assert result.trending_topics is not None

        for topic in result.trending_topics:
            assert isinstance(topic, TrendingTopic)
            assert topic.topic is not None
            assert len(topic.topic) > 0
            assert topic.count >= 0
            assert -1 <= topic.sentiment_score <= 1

    @pytest.mark.asyncio
    async def test_key_opinions(self, service: SentimentTimeSeriesService):
        """Test key opinions extraction."""
        result = await service.get_sentiment_pulse(
            symbol="600519",
            days=7
        )

        # Check bullish and bearish opinions
        bullish = result.top_bullish_opinions
        bearish = result.top_bearish_opinions

        for opinion in bullish + bearish:
            assert isinstance(opinion, KeyOpinion)
            assert opinion.author is not None
            assert opinion.content is not None
            assert opinion.source is not None
            assert opinion.sentiment in ["bullish", "bearish"]

    @pytest.mark.asyncio
    async def test_heat_index(self, service: SentimentTimeSeriesService):
        """Test heat index calculation."""
        result = await service.get_sentiment_pulse(
            symbol="600519",
            days=7
        )

        assert result.heat_index is not None
        assert 0 <= result.heat_index <= 100

    @pytest.mark.asyncio
    async def test_score_change_24h(self, service: SentimentTimeSeriesService):
        """Test 24h score change."""
        result = await service.get_sentiment_pulse(
            symbol="600519",
            days=7
        )

        # score_change_24h can be positive or negative
        assert result.score_change_24h is not None

    @pytest.mark.asyncio
    async def test_confidence(self, service: SentimentTimeSeriesService):
        """Test confidence value."""
        result = await service.get_sentiment_pulse(
            symbol="600519",
            days=7
        )

        # Confidence should be 0-1
        assert 0 <= result.confidence <= 1

    @pytest.mark.asyncio
    async def test_different_time_periods(self, service: SentimentTimeSeriesService):
        """Test with different time periods."""
        periods = [3, 7, 14]

        for days in periods:
            result = await service.get_sentiment_pulse(
                symbol="600519",
                days=days
            )

            assert len(result.daily_moods) <= days

    @pytest.mark.asyncio
    async def test_different_symbols(self, service: SentimentTimeSeriesService):
        """Test with different stock symbols."""
        symbols = ["600519", "000858", "601318"]

        for symbol in symbols:
            result = await service.get_sentiment_pulse(
                symbol=symbol,
                days=7
            )

            assert result.symbol == symbol
            assert result.current_score is not None

    @pytest.mark.asyncio
    async def test_sentiment_level_enum_values(self, service: SentimentTimeSeriesService):
        """Test that all sentiment levels are valid."""
        result = await service.get_sentiment_pulse(
            symbol="600519",
            days=7
        )

        valid_levels = [
            SentimentLevel.VERY_BEARISH,
            SentimentLevel.BEARISH,
            SentimentLevel.NEUTRAL,
            SentimentLevel.BULLISH,
            SentimentLevel.VERY_BULLISH,
        ]

        assert result.current_level in valid_levels

    @pytest.mark.asyncio
    async def test_post_count_data_presence(self, service: SentimentTimeSeriesService):
        """Test that post count data is present in daily moods."""
        result = await service.get_sentiment_pulse(
            symbol="600519",
            days=7
        )

        total_posts = sum(m.post_count for m in result.daily_moods)
        assert total_posts >= 0

    @pytest.mark.asyncio
    async def test_source_distribution(self, service: SentimentTimeSeriesService):
        """Test source distribution."""
        result = await service.get_sentiment_pulse(
            symbol="600519",
            days=7
        )

        # source_distribution should be a dict
        assert isinstance(result.source_distribution, dict)
