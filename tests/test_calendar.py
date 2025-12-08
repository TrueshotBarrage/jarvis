"""Tests for the Calendar API module."""

from unittest.mock import MagicMock, patch

import pytest

from apis.calendar import CalendarAPI, CalendarAPIError


class TestCalendarAPIInit:
    """Test suite for CalendarAPI initialization."""

    @patch("apis.calendar.settings")
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

    @patch("apis.calendar.build")
    @patch("apis.calendar.service_account.Credentials.from_service_account_file")
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

    @patch("apis.calendar.build")
    @patch("apis.calendar.service_account.Credentials.from_service_account_file")
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
