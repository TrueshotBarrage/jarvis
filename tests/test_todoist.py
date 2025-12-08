"""Tests for the Todoist API module."""

from unittest.mock import MagicMock, patch

import pytest

from apis.todoist import TodoistAPI, TodoistAPIError


class TestTodoistAPIInit:
    """Test suite for TodoistAPI initialization."""

    def test_default_initialization(self):
        """Test TodoistAPI initializes with default values."""
        with patch("apis.todoist.settings") as mock_settings:
            mock_settings.todoist_api_token = "test-token"
            api = TodoistAPI()
            assert api._token is None  # Token loaded lazily


class TestTodoistAPIGetToken:
    """Test suite for TodoistAPI token loading."""

    def test_raises_error_when_token_not_configured(self):
        """Test that missing token raises TodoistAPIError."""
        with patch("apis.todoist.settings") as mock_settings:
            mock_settings.todoist_api_token = None
            api = TodoistAPI()
            with pytest.raises(TodoistAPIError) as exc_info:
                api._get_token()
            assert "TODOIST_API_TOKEN not configured" in str(exc_info.value)

    def test_loads_token_successfully(self):
        """Test successful token loading from config."""
        with patch("apis.todoist.settings") as mock_settings:
            mock_settings.todoist_api_token = "test_token"
            api = TodoistAPI()
            token = api._get_token()
            assert token == "test_token"

    def test_caches_token(self):
        """Test that token is cached after first load."""
        with patch("apis.todoist.settings") as mock_settings:
            mock_settings.todoist_api_token = "test_token"
            api = TodoistAPI()
            token1 = api._get_token()
            token2 = api._get_token()
            assert token1 == token2


class TestTodoistAPIGetTasks:
    """Test suite for TodoistAPI.get_tasks method."""

    @patch("apis.todoist.requests.get")
    def test_get_tasks_returns_formatted_tasks(self, mock_get):
        """Test get_tasks returns properly formatted tasks."""
        with patch("apis.todoist.settings") as mock_settings:
            mock_settings.todoist_api_token = "test_token"

            mock_response = MagicMock()
            mock_response.json.return_value = [
                {
                    "id": "123",
                    "content": "Buy groceries",
                    "description": "",
                    "priority": 4,
                    "project_id": "456",
                    "labels": ["shopping"],
                    "due": {
                        "date": "2025-01-01",
                        "datetime": None,
                        "string": "Jan 1",
                        "is_recurring": False,
                    },
                }
            ]
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            api = TodoistAPI()
            tasks = api.get_tasks()

            assert len(tasks) == 1
            assert tasks[0]["content"] == "Buy groceries"
            assert tasks[0]["priority"] == 4

    @patch("apis.todoist.requests.get")
    def test_get_tasks_with_date_filter(self, mock_get):
        """Test get_tasks passes date filter to API."""
        with patch("apis.todoist.settings") as mock_settings:
            mock_settings.todoist_api_token = "test_token"

            mock_response = MagicMock()
            mock_response.json.return_value = []
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            api = TodoistAPI()
            api.get_tasks(date="2025-01-01")

            _, kwargs = mock_get.call_args
            assert kwargs["params"]["filter"] == "due: 2025-01-01"

    @patch("apis.todoist.requests.get")
    def test_get_tasks_without_date(self, mock_get):
        """Test get_tasks works without date filter."""
        with patch("apis.todoist.settings") as mock_settings:
            mock_settings.todoist_api_token = "test_token"

            mock_response = MagicMock()
            mock_response.json.return_value = []
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            api = TodoistAPI()
            api.get_tasks()

            _, kwargs = mock_get.call_args
            assert "filter" not in kwargs.get("params", {})

    @patch("apis.todoist.requests.get")
    def test_get_tasks_handles_no_due_date(self, mock_get):
        """Test get_tasks handles tasks without due dates."""
        with patch("apis.todoist.settings") as mock_settings:
            mock_settings.todoist_api_token = "test_token"

            mock_response = MagicMock()
            mock_response.json.return_value = [
                {
                    "id": "123",
                    "content": "Task without due date",
                    "description": "",
                    "priority": 1,
                    "project_id": "456",
                    "labels": [],
                }
            ]
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            api = TodoistAPI()
            tasks = api.get_tasks()

            assert len(tasks) == 1
            assert tasks[0]["due"] is None


class TestTodoistAPIFormatTask:
    """Test suite for TodoistAPI._format_task method."""

    def test_format_task_with_due_date(self):
        """Test _format_task formats task with due date."""
        with patch("apis.todoist.settings") as mock_settings:
            mock_settings.todoist_api_token = "test_token"

            api = TodoistAPI()
            task = {
                "id": "123",
                "content": "Test task",
                "description": "Test description",
                "priority": 2,
                "project_id": "456",
                "labels": ["label1"],
                "due": {
                    "date": "2025-01-01",
                    "datetime": "2025-01-01T10:00:00",
                    "string": "Jan 1",
                    "is_recurring": True,
                },
            }

            result = api._format_task(task)

            assert result["id"] == "123"
            assert result["content"] == "Test task"
            assert result["due"]["date"] == "2025-01-01"
            assert result["due"]["is_recurring"] is True

    def test_format_task_without_due_date(self):
        """Test _format_task handles task without due date."""
        with patch("apis.todoist.settings") as mock_settings:
            mock_settings.todoist_api_token = "test_token"

            api = TodoistAPI()
            task = {
                "id": "123",
                "content": "Test task",
            }

            result = api._format_task(task)

            assert result["due"] is None
