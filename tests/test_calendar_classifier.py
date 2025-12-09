"""Tests for the Calendar Classifier module."""

from unittest.mock import patch

from jarvis.calendar_classifier import (
    CalendarType,
    classify_calendar,
    get_calendar_types,
)


class TestCalendarType:
    """Test suite for CalendarType enum."""

    def test_all_types_defined(self):
        """Test that all expected types exist."""
        assert CalendarType.BIRTHDAYS.value == "birthdays"
        assert CalendarType.SOCIAL.value == "social"
        assert CalendarType.WORK.value == "work"
        assert CalendarType.PERSONAL.value == "personal"
        assert CalendarType.RECURRING.value == "recurring"
        assert CalendarType.UNKNOWN.value == "unknown"


class TestClassifyCalendar:
    """Test suite for classify_calendar function."""

    def test_birthdays_calendar(self):
        """Test birthday calendar detection."""
        assert classify_calendar("Birthdays") == CalendarType.BIRTHDAYS
        assert classify_calendar("Birthday Reminders") == CalendarType.BIRTHDAYS
        assert classify_calendar("bday") == CalendarType.BIRTHDAYS

    def test_social_calendar(self):
        """Test social calendar detection."""
        assert classify_calendar("Food") == CalendarType.SOCIAL
        assert classify_calendar("Drinks with Friends") == CalendarType.SOCIAL
        assert classify_calendar("Lunch Plans") == CalendarType.SOCIAL
        assert classify_calendar("Dinner") == CalendarType.SOCIAL
        assert classify_calendar("Coffee") == CalendarType.SOCIAL

    def test_work_calendar(self):
        """Test work calendar detection."""
        assert classify_calendar("Work") == CalendarType.WORK
        assert classify_calendar("Office Meetings") == CalendarType.WORK
        assert classify_calendar("Job Tasks") == CalendarType.WORK

    def test_personal_calendar(self):
        """Test personal calendar detection."""
        assert classify_calendar("Personal") == CalendarType.PERSONAL
        assert classify_calendar("My Calendar") == CalendarType.PERSONAL
        assert classify_calendar("Private") == CalendarType.PERSONAL

    def test_recurring_calendar(self):
        """Test recurring calendar detection."""
        assert classify_calendar("Bills") == CalendarType.RECURRING
        assert classify_calendar("Recurring Events") == CalendarType.RECURRING
        assert classify_calendar("Chores") == CalendarType.RECURRING

    def test_unknown_calendar(self):
        """Test unknown calendar fallback."""
        assert classify_calendar("Random Calendar") == CalendarType.UNKNOWN
        assert classify_calendar("XYZ") == CalendarType.UNKNOWN

    def test_case_insensitive(self):
        """Test that matching is case-insensitive."""
        assert classify_calendar("BIRTHDAYS") == CalendarType.BIRTHDAYS
        assert classify_calendar("FOOD") == CalendarType.SOCIAL
        assert classify_calendar("work") == CalendarType.WORK

    @patch("jarvis.config.settings")
    def test_override_from_config(self, mock_settings):
        """Test config override takes precedence."""
        mock_settings.calendar_type_overrides = '{"Custom Cal": "social"}'
        assert classify_calendar("Custom Cal") == CalendarType.SOCIAL

    @patch("jarvis.config.settings")
    def test_override_beats_pattern(self, mock_settings):
        """Test override beats pattern matching."""
        mock_settings.calendar_type_overrides = '{"Work": "personal"}'
        # "Work" would match work pattern, but override says personal
        assert classify_calendar("Work") == CalendarType.PERSONAL


class TestGetCalendarTypes:
    """Test suite for get_calendar_types function."""

    def test_multiple_calendars(self):
        """Test classifying multiple calendars at once."""
        names = ["Birthdays", "Food", "Work", "Random"]
        result = get_calendar_types(names)

        assert result["Birthdays"] == CalendarType.BIRTHDAYS
        assert result["Food"] == CalendarType.SOCIAL
        assert result["Work"] == CalendarType.WORK
        assert result["Random"] == CalendarType.UNKNOWN
