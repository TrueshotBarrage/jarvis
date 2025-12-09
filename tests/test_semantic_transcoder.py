"""Tests for the Semantic Transcoder module."""

from datetime import date, timedelta

import pytest

from jarvis.semantic_transcoder import SemanticTranscoder, TranscoderConfig


class TestDateTimeFormatting:
    """Tests for date and time formatting methods."""

    @pytest.fixture
    def transcoder(self):
        """Create a transcoder instance."""
        return SemanticTranscoder()

    def test_format_date_full(self, transcoder):
        """Test full date formatting."""
        result = transcoder.format_date_full("2025-12-09")
        assert result == "Tuesday, December 9th, 2025"

    def test_format_date_full_with_datetime(self, transcoder):
        """Test full date formatting from datetime string."""
        result = transcoder.format_date_full("2025-12-09T10:00:00-05:00")
        assert result == "Tuesday, December 9th, 2025"

    def test_format_date_full_date_object(self, transcoder):
        """Test full date formatting from date object."""
        result = transcoder.format_date_full(date(2025, 12, 9))
        assert result == "Tuesday, December 9th, 2025"

    def test_format_date_short(self, transcoder):
        """Test short date formatting."""
        result = transcoder.format_date_short("2025-12-09")
        assert result == "Dec 9"

    def test_format_time_am(self, transcoder):
        """Test time formatting for AM."""
        result = transcoder.format_time("2025-12-09T09:30:00-05:00")
        assert result == "9:30 AM"

    def test_format_time_pm(self, transcoder):
        """Test time formatting for PM."""
        result = transcoder.format_time("2025-12-09T14:00:00-05:00")
        assert result == "2:00 PM"

    def test_format_time_noon(self, transcoder):
        """Test time formatting for noon."""
        result = transcoder.format_time("2025-12-09T12:00:00-05:00")
        assert result == "12:00 PM"

    def test_format_time_midnight(self, transcoder):
        """Test time formatting for midnight."""
        result = transcoder.format_time("2025-12-09T00:00:00-05:00")
        assert result == "12:00 AM"

    def test_format_time_all_day(self, transcoder):
        """Test time formatting for date-only (all day event)."""
        result = transcoder.format_time("2025-12-09")
        assert result == "All day"

    def test_format_time_24h(self):
        """Test 24-hour time formatting."""
        config = TranscoderConfig(time_format_24h=True)
        transcoder = SemanticTranscoder(config)
        result = transcoder.format_time("2025-12-09T14:30:00-05:00")
        assert result == "14:30"


class TestDaySuffix:
    """Tests for ordinal day suffix."""

    @pytest.fixture
    def transcoder(self):
        return SemanticTranscoder()

    def test_suffix_1st(self, transcoder):
        assert transcoder._get_day_suffix(1) == "st"

    def test_suffix_2nd(self, transcoder):
        assert transcoder._get_day_suffix(2) == "nd"

    def test_suffix_3rd(self, transcoder):
        assert transcoder._get_day_suffix(3) == "rd"

    def test_suffix_4th(self, transcoder):
        assert transcoder._get_day_suffix(4) == "th"

    def test_suffix_11th(self, transcoder):
        assert transcoder._get_day_suffix(11) == "th"

    def test_suffix_12th(self, transcoder):
        assert transcoder._get_day_suffix(12) == "th"

    def test_suffix_13th(self, transcoder):
        assert transcoder._get_day_suffix(13) == "th"

    def test_suffix_21st(self, transcoder):
        assert transcoder._get_day_suffix(21) == "st"

    def test_suffix_22nd(self, transcoder):
        assert transcoder._get_day_suffix(22) == "nd"

    def test_suffix_23rd(self, transcoder):
        assert transcoder._get_day_suffix(23) == "rd"


class TestRelativeDateLabel:
    """Tests for relative date labels."""

    @pytest.fixture
    def transcoder(self):
        return SemanticTranscoder()

    def test_today_label(self, transcoder):
        """Test TODAY label for today's date."""
        today = date.today()
        result = transcoder.get_relative_date_label(today)
        assert result == "TODAY"

    def test_tomorrow_label(self, transcoder):
        """Test TOMORROW label for tomorrow's date."""
        tomorrow = date.today() + timedelta(days=1)
        result = transcoder.get_relative_date_label(tomorrow)
        assert result == "TOMORROW"

    def test_no_label_for_other_dates(self, transcoder):
        """Test None for dates beyond tomorrow."""
        next_week = date.today() + timedelta(days=7)
        result = transcoder.get_relative_date_label(next_week)
        assert result is None


class TestWeatherTranscoding:
    """Tests for weather data transcoding."""

    @pytest.fixture
    def transcoder(self):
        return SemanticTranscoder()

    @pytest.fixture
    def sample_weather(self):
        """Sample weather API response."""
        return {
            "current": {"temperature_2m": 45.2, "precipitation": 0},
            "current_units": {"temperature_2m": "°F", "precipitation": "mm"},
            "daily": {
                "time": ["2025-12-08", "2025-12-09"],
                "temperature_2m_max": [52.1, 48.3],
                "temperature_2m_min": [38.5, 35.2],
                "sunrise": ["2025-12-08T07:05", "2025-12-09T07:06"],
                "sunset": ["2025-12-08T16:32", "2025-12-09T16:32"],
            },
        }

    def test_transcode_weather_current(self, transcoder, sample_weather):
        """Test current weather transcoding."""
        result = transcoder.transcode_weather(sample_weather)
        assert "CURRENT WEATHER:" in result
        assert "Temperature: 45°F" in result
        assert "Precipitation: None" in result

    def test_transcode_weather_daily(self, transcoder, sample_weather):
        """Test daily forecast transcoding."""
        result = transcoder.transcode_weather(sample_weather)
        assert "High: 52°F, Low: 38°F" in result  # 38.5 rounds to 38

    def test_transcode_weather_empty(self, transcoder):
        """Test empty weather data handling."""
        result = transcoder.transcode_weather({})
        assert result == "Weather data unavailable."


class TestEventsTranscoding:
    """Tests for calendar events transcoding."""

    @pytest.fixture
    def transcoder(self):
        return SemanticTranscoder()

    @pytest.fixture
    def sample_events(self):
        """Sample calendar events."""
        return [
            {
                "summary": "Team Meeting",
                "start": "2025-12-09T10:00:00-05:00",
                "end": "2025-12-09T11:00:00-05:00",
                "calendar": "Work",
                "location": "Room 101",
            },
            {
                "summary": "Lunch with Sarah",
                "start": "2025-12-09T12:30:00-05:00",
                "calendar": "Food",
            },
            {
                "summary": "Birthday: Mom",
                "start": "2025-12-10",
                "calendar": "Birthdays",
                "calendar_type": "birthdays",
            },
        ]

    def test_transcode_events_formats_times(self, transcoder, sample_events):
        """Test event time formatting."""
        result = transcoder.transcode_events(sample_events)
        assert "10:00 AM - 11:00 AM: Team Meeting" in result

    def test_transcode_events_includes_location(self, transcoder, sample_events):
        """Test location inclusion."""
        result = transcoder.transcode_events(sample_events)
        assert "Room 101" in result

    def test_transcode_events_includes_calendar(self, transcoder, sample_events):
        """Test calendar name inclusion."""
        result = transcoder.transcode_events(sample_events)
        assert "Work calendar" in result

    def test_transcode_events_groups_by_date(self, transcoder, sample_events):
        """Test events are grouped by date."""
        result = transcoder.transcode_events(sample_events)
        assert "December 9th" in result
        assert "December 10th" in result

    def test_transcode_events_all_day(self, transcoder, sample_events):
        """Test all-day event handling."""
        result = transcoder.transcode_events(sample_events)
        assert "(all day)" in result

    def test_transcode_events_birthday_emoji(self, transcoder, sample_events):
        """Test birthday emoji."""
        result = transcoder.transcode_events(sample_events)
        assert "🎂" in result

    def test_transcode_events_no_emoji(self, sample_events):
        """Test without emoji."""
        config = TranscoderConfig(use_emoji=False)
        transcoder = SemanticTranscoder(config)
        result = transcoder.transcode_events(sample_events)
        assert "🎂" not in result
        assert "📍" not in result

    def test_transcode_events_empty(self, transcoder):
        """Test empty events handling."""
        result = transcoder.transcode_events([])
        assert "No events scheduled" in result

    def test_transcode_events_count(self, transcoder, sample_events):
        """Test event count in per-day summary."""
        result = transcoder.transcode_events(sample_events)
        assert "(2 events)" in result  # 2 events on Dec 9
        assert "(1 event)" in result  # 1 event on Dec 10


class TestTodosTranscoding:
    """Tests for todo list transcoding."""

    @pytest.fixture
    def transcoder(self):
        return SemanticTranscoder()

    @pytest.fixture
    def sample_todos(self):
        """Sample todo list."""
        return [
            {"content": "Buy groceries", "due": {"date": "2025-12-08"}, "priority": 4},
            {"content": "Call dentist", "due": {"date": "2025-12-08"}, "priority": 1},
            {"content": "Review PR", "due": {"date": "2025-12-09"}, "priority": 3},
            {"content": "Someday task", "priority": 1},
        ]

    def test_transcode_todos_groups_by_date(self, transcoder, sample_todos):
        """Test todos are grouped by date."""
        result = transcoder.transcode_todos(sample_todos)
        assert "December 8th" in result
        assert "December 9th" in result

    def test_transcode_todos_priority_high(self, transcoder, sample_todos):
        """Test high priority indicator."""
        result = transcoder.transcode_todos(sample_todos)
        assert "[!] Buy groceries (high priority)" in result

    def test_transcode_todos_priority_medium(self, transcoder, sample_todos):
        """Test medium priority indicator."""
        result = transcoder.transcode_todos(sample_todos)
        assert "[-] Review PR (medium priority)" in result

    def test_transcode_todos_no_due_date(self, transcoder, sample_todos):
        """Test tasks without due date."""
        result = transcoder.transcode_todos(sample_todos)
        assert "TASKS (no due date):" in result
        assert "Someday task" in result

    def test_transcode_todos_empty(self, transcoder):
        """Test empty todos handling."""
        result = transcoder.transcode_todos([])
        assert result == "No tasks scheduled."

    def test_transcode_todos_count(self, transcoder, sample_todos):
        """Test task count in summary."""
        result = transcoder.transcode_todos(sample_todos)
        assert "Total: 4 tasks" in result


class TestTranscodeAll:
    """Tests for combined transcoding."""

    @pytest.fixture
    def transcoder(self):
        return SemanticTranscoder()

    def test_transcode_all_weather_only(self, transcoder):
        """Test transcoding weather only."""
        data = {
            "weather": {
                "current": {"temperature_2m": 45, "precipitation": 0},
                "current_units": {"temperature_2m": "°F"},
            }
        }
        result = transcoder.transcode_all(data)
        assert "CURRENT WEATHER:" in result

    def test_transcode_all_events_only(self, transcoder):
        """Test transcoding events only."""
        data = {
            "events": [
                {"summary": "Test", "start": "2025-12-09T10:00:00-05:00", "calendar": "Work"}
            ]
        }
        result = transcoder.transcode_all(data)
        assert "Test" in result
        assert "Work calendar" in result

    def test_transcode_all_combined(self, transcoder):
        """Test transcoding multiple data types."""
        data = {
            "weather": {
                "current": {"temperature_2m": 45, "precipitation": 0},
                "current_units": {"temperature_2m": "°F"},
            },
            "events": [
                {"summary": "Meeting", "start": "2025-12-09T10:00:00-05:00", "calendar": "Work"}
            ],
            "todos": [{"content": "Task 1", "due": {"date": "2025-12-08"}, "priority": 4}],
        }
        result = transcoder.transcode_all(data)
        assert "CURRENT WEATHER:" in result
        assert "Meeting" in result
        assert "Task 1" in result
        assert "---" in result  # Section separator

    def test_transcode_all_empty(self, transcoder):
        """Test transcoding empty data."""
        result = transcoder.transcode_all({})
        assert result == "No data available."
