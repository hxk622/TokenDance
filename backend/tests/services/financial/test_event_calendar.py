"""
Unit tests for EventCalendarService.

Run with:
    cd backend && uv run pytest tests/services/financial/test_event_calendar.py -v
"""

from datetime import date, datetime, timedelta

import pytest

from app.services.financial.event.event_calendar import (
    EventCalendarResult,
    EventCalendarService,
    EventImpact,
    EventImportance,
    EventType,
    UpcomingEvent,
)


class TestEventCalendarService:
    """Tests for EventCalendarService."""

    @pytest.fixture
    def service(self) -> EventCalendarService:
        """Create service instance."""
        return EventCalendarService()

    @pytest.mark.asyncio
    async def test_get_upcoming_events_basic(self, service: EventCalendarService):
        """Test getting upcoming events."""
        result = await service.get_upcoming_events(
            symbol="600519",
            days_ahead=90
        )

        assert isinstance(result, EventCalendarResult)
        assert result.symbol == "600519"
        events = result.upcoming_events
        assert isinstance(events, list)

        for event in events:
            assert isinstance(event, UpcomingEvent)
            assert event.symbol == "600519"
            assert event.event_type is not None
            assert event.event_date is not None
            assert event.importance is not None

    @pytest.mark.asyncio
    async def test_upcoming_events_date_range(self, service: EventCalendarService):
        """Test that upcoming events are within the specified date range."""
        days_ahead = 30
        result = await service.get_upcoming_events(
            symbol="600519",
            days_ahead=days_ahead
        )

        today = date.today()
        end_date = today + timedelta(days=days_ahead)

        for event in result.upcoming_events:
            event_date = event.event_date
            if isinstance(event_date, datetime):
                event_date = event_date.date()
            assert today <= event_date <= end_date, (
                f"Event date {event_date} not in range [{today}, {end_date}]"
            )

    @pytest.mark.asyncio
    async def test_upcoming_events_sorted_by_date(self, service: EventCalendarService):
        """Test that events are sorted by date."""
        result = await service.get_upcoming_events(
            symbol="600519",
            days_ahead=90
        )
        events = result.upcoming_events

        if len(events) > 1:
            for i in range(len(events) - 1):
                current_date = events[i].event_date
                next_date = events[i + 1].event_date
                assert current_date <= next_date, "Events should be sorted by date"

    @pytest.mark.asyncio
    async def test_event_types(self, service: EventCalendarService):
        """Test that event types are valid."""
        result = await service.get_upcoming_events(
            symbol="600519",
            days_ahead=90
        )

        valid_types = set(EventType)

        for event in result.upcoming_events:
            assert event.event_type in valid_types

    @pytest.mark.asyncio
    async def test_event_importance_levels(self, service: EventCalendarService):
        """Test that importance levels are valid."""
        result = await service.get_upcoming_events(
            symbol="600519",
            days_ahead=90
        )

        valid_importance = set(EventImportance)

        for event in result.upcoming_events:
            assert event.importance in valid_importance

    @pytest.mark.asyncio
    async def test_events_by_type_stat(self, service: EventCalendarService):
        """Test events_by_type statistics."""
        result = await service.get_upcoming_events(
            symbol="600519",
            days_ahead=90
        )

        # events_by_type should be a dict
        assert isinstance(result.events_by_type, dict)

    @pytest.mark.asyncio
    async def test_historical_impacts(self, service: EventCalendarService):
        """Test historical event impacts."""
        result = await service.get_upcoming_events(
            symbol="600519",
            days_ahead=90
        )

        for impact in result.historical_impacts:
            assert isinstance(impact, EventImpact)
            assert impact.event_type is not None
            assert impact.price_change_1d is not None

    @pytest.mark.asyncio
    async def test_event_has_title(self, service: EventCalendarService):
        """Test that events have titles."""
        result = await service.get_upcoming_events(
            symbol="600519",
            days_ahead=90
        )

        for event in result.upcoming_events:
            assert event.title is not None
            assert len(event.title) > 0

    @pytest.mark.asyncio
    async def test_days_until_calculation(self, service: EventCalendarService):
        """Test that days_until is calculated correctly."""
        result = await service.get_upcoming_events(
            symbol="600519",
            days_ahead=90
        )

        today = date.today()

        for event in result.upcoming_events:
            event_date = event.event_date
            if isinstance(event_date, datetime):
                event_date = event_date.date()
            expected_days = (event_date - today).days
            assert event.days_until == expected_days

    @pytest.mark.asyncio
    async def test_empty_result_for_very_short_range(
        self, service: EventCalendarService
    ):
        """Test with very short time range might return empty or few results."""
        result = await service.get_upcoming_events(
            symbol="600519",
            days_ahead=1  # Only 1 day ahead
        )

        # Should return a valid result
        assert isinstance(result, EventCalendarResult)

    @pytest.mark.asyncio
    async def test_different_symbols(self, service: EventCalendarService):
        """Test with different stock symbols."""
        symbols = ["600519", "000858", "601318"]

        for symbol in symbols:
            result = await service.get_upcoming_events(
                symbol=symbol,
                days_ahead=90
            )

            assert result.symbol == symbol
            for event in result.upcoming_events:
                assert event.symbol == symbol
