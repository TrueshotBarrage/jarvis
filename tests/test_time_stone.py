"""Tests for the Time Stone temporal expression parser module."""

from datetime import date, timedelta

import pytest

from jarvis.time_stone import (
    TemporalParser,
    TemporalPattern,
    TimeRange,
    detect_temporal_intent,
    parse_time_range,
)


class TestTimeRange:
    """Tests for TimeRange dataclass."""

    def test_is_single_day_true(self):
        """Test is_single_day returns True for same start/end."""
        today = date.today()
        tr = TimeRange(start=today, end=today, description="today")
        assert tr.is_single_day is True

    def test_is_single_day_false(self):
        """Test is_single_day returns False for different start/end."""
        today = date.today()
        tr = TimeRange(start=today, end=today + timedelta(days=1), description="range")
        assert tr.is_single_day is False

    def test_days_single(self):
        """Test days returns 1 for single day."""
        today = date.today()
        tr = TimeRange(start=today, end=today, description="today")
        assert tr.days == 1

    def test_days_week(self):
        """Test days returns 7 for a week."""
        today = date.today()
        tr = TimeRange(start=today, end=today + timedelta(days=6), description="week")
        assert tr.days == 7

    def test_factory_today(self):
        """Test TimeRange.today() factory method."""
        tr = TimeRange.today()
        today = date.today()
        assert tr.start == today
        assert tr.end == today
        assert tr.description == "today"
        assert tr.pattern == TemporalPattern.TODAY

    def test_factory_tomorrow(self):
        """Test TimeRange.tomorrow() factory method."""
        tr = TimeRange.tomorrow()
        tomorrow = date.today() + timedelta(days=1)
        assert tr.start == tomorrow
        assert tr.end == tomorrow
        assert tr.description == "tomorrow"
        assert tr.pattern == TemporalPattern.TOMORROW

    def test_factory_this_week(self):
        """Test TimeRange.this_week() factory method."""
        tr = TimeRange.this_week()
        today = date.today()
        expected_monday = today - timedelta(days=today.weekday())
        expected_sunday = expected_monday + timedelta(days=6)
        assert tr.start == expected_monday
        assert tr.end == expected_sunday
        assert tr.description == "this week"
        assert tr.days == 7

    def test_factory_next_week(self):
        """Test TimeRange.next_week() factory method."""
        tr = TimeRange.next_week()
        today = date.today()
        days_until_monday = 7 - today.weekday()
        expected_monday = today + timedelta(days=days_until_monday)
        expected_sunday = expected_monday + timedelta(days=6)
        assert tr.start == expected_monday
        assert tr.end == expected_sunday
        assert tr.description == "next week"

    def test_factory_next_n_days(self):
        """Test TimeRange.next_n_days() factory method."""
        tr = TimeRange.next_n_days(5)
        today = date.today()
        assert tr.start == today
        assert tr.end == today + timedelta(days=4)
        assert tr.description == "next 5 days"
        assert tr.days == 5


class TestTemporalParser:
    """Tests for TemporalParser class."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return TemporalParser()

    @pytest.fixture
    def reference_date(self):
        """Fixed reference date for testing: Wednesday, December 11, 2024."""
        return date(2024, 12, 11)

    def test_parse_today(self, parser, reference_date):
        """Test parsing 'today'."""
        result = parser.parse("What's on my calendar today?", reference_date)
        assert result is not None
        assert result.start == reference_date
        assert result.end == reference_date
        assert result.pattern == TemporalPattern.TODAY

    def test_parse_tomorrow(self, parser, reference_date):
        """Test parsing 'tomorrow'."""
        result = parser.parse("Any meetings tomorrow?", reference_date)
        expected = reference_date + timedelta(days=1)
        assert result is not None
        assert result.start == expected
        assert result.end == expected
        assert result.pattern == TemporalPattern.TOMORROW

    def test_parse_yesterday(self, parser, reference_date):
        """Test parsing 'yesterday'."""
        result = parser.parse("What did I have yesterday?", reference_date)
        expected = reference_date - timedelta(days=1)
        assert result is not None
        assert result.start == expected
        assert result.end == expected

    def test_parse_this_week(self, parser, reference_date):
        """Test parsing 'this week'."""
        result = parser.parse("What events this week?", reference_date)
        assert result is not None
        # reference_date is Wednesday (weekday 2)
        expected_monday = reference_date - timedelta(days=2)  # Dec 9
        expected_sunday = expected_monday + timedelta(days=6)  # Dec 15
        assert result.start == expected_monday
        assert result.end == expected_sunday
        assert result.pattern == TemporalPattern.THIS_WEEK

    def test_parse_next_week(self, parser, reference_date):
        """Test parsing 'next week'."""
        result = parser.parse("Events next week?", reference_date)
        assert result is not None
        # reference_date is Wednesday (weekday 2), next Monday is Dec 16
        expected_monday = reference_date + timedelta(days=5)  # Dec 16
        expected_sunday = expected_monday + timedelta(days=6)  # Dec 22
        assert result.start == expected_monday
        assert result.end == expected_sunday
        assert result.pattern == TemporalPattern.NEXT_WEEK

    def test_parse_next_n_days(self, parser, reference_date):
        """Test parsing 'next N days'."""
        result = parser.parse("What's happening the next 3 days?", reference_date)
        assert result is not None
        assert result.start == reference_date
        assert result.end == reference_date + timedelta(days=2)
        assert result.pattern == TemporalPattern.NEXT_N_DAYS

    def test_parse_next_n_days_limits_to_30(self, parser, reference_date):
        """Test that large N is capped at 30 days."""
        result = parser.parse("Events for the next 100 days", reference_date)
        assert result is not None
        assert result.days <= 30

    def test_parse_weekday_future(self, parser, reference_date):
        """Test parsing a weekday that's in the future this week."""
        # reference_date is Wednesday, Friday is in 2 days
        result = parser.parse("Any meetings Friday?", reference_date)
        assert result is not None
        expected = reference_date + timedelta(days=2)  # Dec 13
        assert result.start == expected
        assert result.pattern == TemporalPattern.SPECIFIC_WEEKDAY

    def test_parse_weekday_next_prefix(self, parser, reference_date):
        """Test parsing 'next Monday' always means next week's Monday."""
        # reference_date is Wednesday
        result = parser.parse("Events next Monday?", reference_date)
        assert result is not None
        # Next Monday is Dec 16 (5 days from Wednesday Dec 11)
        expected = reference_date + timedelta(days=5)
        assert result.start == expected

    def test_parse_no_temporal_expression(self, parser):
        """Test that non-temporal messages return None."""
        result = parser.parse("Hello, how are you?")
        assert result is None

    def test_parse_case_insensitive(self, parser, reference_date):
        """Test that parsing is case-insensitive."""
        result = parser.parse("TOMORROW", reference_date)
        assert result is not None
        assert result.pattern == TemporalPattern.TOMORROW


class TestModuleFunctions:
    """Tests for module-level convenience functions."""

    def test_parse_time_range_returns_result(self):
        """Test parse_time_range convenience function."""
        result = parse_time_range("What's happening tomorrow?")
        assert result is not None
        assert result.pattern == TemporalPattern.TOMORROW

    def test_parse_time_range_returns_none(self):
        """Test parse_time_range returns None for non-temporal."""
        result = parse_time_range("Hello world")
        assert result is None

    def test_detect_temporal_intent_true(self):
        """Test detect_temporal_intent returns True for temporal queries."""
        assert detect_temporal_intent("tomorrow") is True
        assert detect_temporal_intent("this week") is True
        assert detect_temporal_intent("next Monday") is True
        assert detect_temporal_intent("next 3 days") is True

    def test_detect_temporal_intent_false(self):
        """Test detect_temporal_intent returns False for non-temporal queries."""
        assert detect_temporal_intent("hello") is False
        assert detect_temporal_intent("what is your name") is False
