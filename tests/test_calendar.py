"""Tests for the Calendar API module."""

from unittest.mock import MagicMock, patch

import pytest

from jarvis.apis.calendar import CalendarAPI, CalendarAPIError


class TestCalendarAPIInit:
    """Test suite for CalendarAPI initialization."""

    @patch("jarvis.apis.calendar.settings")
    def test_default_initialization(self, mock_settings):
        """Test CalendarAPI initializes with default values."""
        mock_settings.google_credentials_path = "google_credentials.json"
        mock_settings.google_calendar_id = None

        api = CalendarAPI()
        assert api.credentials_path == "google_credentials.json"
        assert api.calendar_id is None
        assert api._service is None

    def test_custom_credentials_path(self):
        """Test CalendarAPI accepts custom credentials path."""
        api = CalendarAPI(credentials_path="/custom/path.json")
        assert api.credentials_path == "/custom/path.json"

    def test_custom_calendar_id(self):
        """Test CalendarAPI accepts custom calendar ID."""
        api = CalendarAPI(calendar_id="test@gmail.com")
        assert api.calendar_id == "test@gmail.com"

    def test_set_calendar_id_returns_self(self):
        """Test set_calendar_id enables method chaining."""
        api = CalendarAPI()
        result = api.set_calendar_id("new@gmail.com")
        assert result is api
        assert api.calendar_id == "new@gmail.com"


class TestCalendarAPIGetService:
    """Test suite for CalendarAPI service initialization."""

    def test_raises_error_when_credentials_missing(self):
        """Test that missing credentials file raises CalendarAPIError."""
        api = CalendarAPI(credentials_path="nonexistent.json")
        with pytest.raises(CalendarAPIError) as exc_info:
            api._get_service()
        assert "Credentials file not found" in str(exc_info.value)

    @patch("jarvis.apis.calendar.build")
    @patch("jarvis.apis.calendar.service_account.Credentials.from_service_account_file")
    @patch("pathlib.Path.exists")
    def test_creates_service_successfully(self, mock_exists, mock_creds, mock_build):
        """Test successful service creation with valid credentials."""
        mock_exists.return_value = True
        mock_creds.return_value = MagicMock()
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        api = CalendarAPI()
        service = api._get_service()

        assert service is mock_service
        mock_creds.assert_called_once()
        mock_build.assert_called_once_with("calendar", "v3", credentials=mock_creds.return_value)

    @patch("jarvis.apis.calendar.build")
    @patch("jarvis.apis.calendar.service_account.Credentials.from_service_account_file")
    @patch("pathlib.Path.exists")
    def test_caches_service(self, mock_exists, mock_creds, mock_build):
        """Test that service is cached after first initialization."""
        mock_exists.return_value = True
        mock_creds.return_value = MagicMock()
        mock_build.return_value = MagicMock()

        api = CalendarAPI()
        service1 = api._get_service()
        service2 = api._get_service()

        assert service1 is service2
        # Build should only be called once
        mock_build.assert_called_once()


class TestCalendarAPIGetEvents:
    """Test suite for CalendarAPI.get_events method."""

    @patch.object(CalendarAPI, "_get_service")
    def test_get_events_returns_formatted_events(self, mock_get_service):
        """Test get_events returns properly formatted events."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_events = {
            "items": [
                {
                    "id": "event1",
                    "summary": "Team Meeting",
                    "start": {"dateTime": "2025-01-15T10:00:00-05:00"},
                    "end": {"dateTime": "2025-01-15T11:00:00-05:00"},
                    "location": "Conference Room A",
                },
                {
                    "id": "event2",
                    "summary": "Lunch",
                    "start": {"date": "2025-01-15"},
                    "end": {"date": "2025-01-15"},
                },
            ]
        }
        mock_service.events().list().execute.return_value = mock_events

        api = CalendarAPI()
        events = api.get_events("2025-01-15")

        assert len(events) == 2
        assert events[0]["summary"] == "Team Meeting"
        assert events[0]["start"] == "2025-01-15T10:00:00-05:00"
        assert events[0]["location"] == "Conference Room A"
        assert events[1]["summary"] == "Lunch"
        assert events[1]["start"] == "2025-01-15"

    @patch.object(CalendarAPI, "_get_service")
    def test_get_events_handles_empty_calendar(self, mock_get_service):
        """Test get_events returns empty list when no events."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        mock_service.events().list().execute.return_value = {"items": []}

        api = CalendarAPI()
        events = api.get_events("2025-01-15")

        assert events == []

    @patch.object(CalendarAPI, "_get_service")
    def test_get_events_handles_missing_fields(self, mock_get_service):
        """Test get_events handles events with missing optional fields."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_events = {
            "items": [
                {
                    "id": "event1",
                    # Missing summary, location, description
                    "start": {"dateTime": "2025-01-15T10:00:00-05:00"},
                    "end": {"dateTime": "2025-01-15T11:00:00-05:00"},
                }
            ]
        }
        mock_service.events().list().execute.return_value = mock_events

        api = CalendarAPI()
        events = api.get_events("2025-01-15")

        assert events[0]["summary"] == "Untitled Event"
        assert events[0]["location"] == ""
        assert events[0]["description"] == ""


class TestCalendarAPIFormatEvent:
    """Test suite for CalendarAPI._format_event method."""

    def test_format_timed_event(self):
        """Test formatting a timed event."""
        api = CalendarAPI()
        raw_event = {
            "id": "123",
            "summary": "Meeting",
            "start": {"dateTime": "2025-01-15T10:00:00-05:00"},
            "end": {"dateTime": "2025-01-15T11:00:00-05:00"},
            "location": "Room 101",
            "description": "Weekly sync",
        }

        formatted = api._format_event(raw_event)

        assert formatted["id"] == "123"
        assert formatted["summary"] == "Meeting"
        assert formatted["start"] == "2025-01-15T10:00:00-05:00"
        assert formatted["end"] == "2025-01-15T11:00:00-05:00"
        assert formatted["location"] == "Room 101"
        assert formatted["description"] == "Weekly sync"

    def test_format_all_day_event(self):
        """Test formatting an all-day event."""
        api = CalendarAPI()
        raw_event = {
            "id": "456",
            "summary": "Holiday",
            "start": {"date": "2025-01-15"},
            "end": {"date": "2025-01-16"},
        }

        formatted = api._format_event(raw_event)

        assert formatted["start"] == "2025-01-15"
        assert formatted["end"] == "2025-01-16"


class TestCalendarAPIMultiCalendar:
    """Test suite for multi-calendar functionality."""

    @patch("jarvis.apis.calendar.settings")
    def test_parses_calendar_ids_from_settings(self, mock_settings):
        """Test calendar_ids are parsed from comma-separated settings."""
        mock_settings.google_credentials_path = "creds.json"
        mock_settings.google_calendar_id = None
        mock_settings.google_calendar_ids = "cal1@gmail.com, cal2@gmail.com, cal3@gmail.com"

        api = CalendarAPI()

        assert len(api.calendar_ids) == 3
        assert "cal1@gmail.com" in api.calendar_ids
        assert "cal2@gmail.com" in api.calendar_ids
        assert "cal3@gmail.com" in api.calendar_ids

    def test_uses_explicit_calendar_ids(self):
        """Test explicit calendar_ids parameter takes priority."""
        api = CalendarAPI(calendar_ids=["explicit1@gmail.com", "explicit2@gmail.com"])

        assert len(api.calendar_ids) == 2
        assert "explicit1@gmail.com" in api.calendar_ids

    @patch("jarvis.apis.calendar.settings")
    def test_falls_back_to_single_calendar_id(self, mock_settings):
        """Test fallback to single calendar_id when no list configured."""
        mock_settings.google_credentials_path = "creds.json"
        mock_settings.google_calendar_id = "single@gmail.com"
        mock_settings.google_calendar_ids = None

        api = CalendarAPI()

        assert api.calendar_ids == ["single@gmail.com"]


class TestCalendarAPIGetAllEvents:
    """Test suite for CalendarAPI.get_all_events method."""

    @patch.object(CalendarAPI, "_get_service")
    def test_get_all_events_aggregates_calendars(self, mock_get_service):
        """Test get_all_events combines events from multiple calendars."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        # Mock calendar info responses
        mock_service.calendars().get().execute.side_effect = [
            {"summary": "Work"},
            {"summary": "Personal"},
        ]

        # Mock events for each calendar
        mock_service.events().list().execute.side_effect = [
            {
                "items": [
                    {
                        "id": "1",
                        "summary": "Meeting",
                        "start": {"dateTime": "2025-01-15T10:00:00-05:00"},
                        "end": {"dateTime": "2025-01-15T11:00:00-05:00"},
                    }
                ]
            },
            {
                "items": [
                    {
                        "id": "2",
                        "summary": "Lunch",
                        "start": {"dateTime": "2025-01-15T12:00:00-05:00"},
                        "end": {"dateTime": "2025-01-15T13:00:00-05:00"},
                    }
                ]
            },
        ]

        api = CalendarAPI(calendar_ids=["work@gmail.com", "personal@gmail.com"])
        events = api.get_all_events("2025-01-15")

        assert len(events) == 2
        # Events should be sorted by start time
        assert events[0]["summary"] == "Meeting"
        assert events[1]["summary"] == "Lunch"

    @patch.object(CalendarAPI, "_get_service")
    def test_get_all_events_raises_when_no_calendars(self, mock_get_service):
        """Test get_all_events raises error when no calendars configured."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        api = CalendarAPI()
        api.calendar_ids = []  # No calendars

        with pytest.raises(CalendarAPIError) as exc_info:
            api.get_all_events("2025-01-15")

        assert "No calendars configured" in str(exc_info.value)

    @patch.object(CalendarAPI, "_get_service")
    def test_get_all_events_includes_calendar_name(self, mock_get_service):
        """Test that events include their source calendar name."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_service.calendars().get().execute.return_value = {"summary": "Work Calendar"}
        mock_service.events().list().execute.return_value = {
            "items": [
                {
                    "id": "1",
                    "summary": "Meeting",
                    "start": {"dateTime": "2025-01-15T10:00:00-05:00"},
                    "end": {"dateTime": "2025-01-15T11:00:00-05:00"},
                }
            ]
        }

        api = CalendarAPI(calendar_ids=["work@gmail.com"])
        events = api.get_all_events("2025-01-15")

        assert events[0]["calendar"] == "Work Calendar"


class TestCalendarAPIGetEventsRange:
    """Test suite for CalendarAPI.get_events_range method."""

    @patch.object(CalendarAPI, "_get_service")
    def test_get_events_range_fetches_date_range(self, mock_get_service):
        """Test get_events_range fetches events across date range."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_service.calendars().get().execute.return_value = {"summary": "Work"}
        mock_service.events().list().execute.return_value = {
            "items": [
                {
                    "id": "1",
                    "summary": "Day 1 Event",
                    "start": {"dateTime": "2025-01-15T10:00:00-05:00"},
                    "end": {"dateTime": "2025-01-15T11:00:00-05:00"},
                },
                {
                    "id": "2",
                    "summary": "Day 2 Event",
                    "start": {"dateTime": "2025-01-16T10:00:00-05:00"},
                    "end": {"dateTime": "2025-01-16T11:00:00-05:00"},
                },
            ]
        }

        api = CalendarAPI(calendar_ids=["work@gmail.com"])
        events = api.get_events_range("2025-01-15", "2025-01-16")

        assert len(events) == 2
        # Each event should have a 'date' field
        assert events[0]["date"] == "2025-01-15"
        assert events[1]["date"] == "2025-01-16"

    def test_get_events_range_validates_date_format(self):
        """Test get_events_range validates date format."""
        api = CalendarAPI(calendar_ids=["test@gmail.com"])

        with pytest.raises(CalendarAPIError) as exc_info:
            api.get_events_range("invalid-date", "2025-01-16")

        assert "Invalid date format" in str(exc_info.value)

    def test_get_events_range_enforces_max_days(self):
        """Test get_events_range limits range to max_days."""
        api = CalendarAPI(calendar_ids=["test@gmail.com"])

        with pytest.raises(ValueError) as exc_info:
            api.get_events_range("2025-01-01", "2025-12-31", max_days=30)

        assert "exceeds maximum" in str(exc_info.value)

    def test_get_events_range_validates_date_order(self):
        """Test get_events_range validates start before end."""
        api = CalendarAPI(calendar_ids=["test@gmail.com"])

        with pytest.raises(ValueError) as exc_info:
            api.get_events_range("2025-01-16", "2025-01-15")

        assert "must be" in str(exc_info.value).lower() and "after" in str(exc_info.value).lower()
