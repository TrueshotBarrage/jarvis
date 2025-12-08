"""Tests for the Todoist API module."""

from unittest.mock import MagicMock, patch

import pytest

from apis.todoist import TodoistAPI, TodoistAPIError


class TestTodoistAPIInit:
    """Test suite for TodoistAPI initialization."""

    def test_default_initialization(self):
        """Test TodoistAPI initializes with default values."""
        api = TodoistAPI()
        assert api.secrets_path == "secrets.json"
        assert api._token is None

    def test_custom_secrets_path(self):
        """Test TodoistAPI accepts custom secrets path."""
        api = TodoistAPI(secrets_path="/custom/secrets.json")
        assert api.secrets_path == "/custom/secrets.json"


class TestTodoistAPIGetToken:
    """Test suite for TodoistAPI token loading."""

    def test_raises_error_when_secrets_missing(self):
        """Test that missing secrets file raises TodoistAPIError."""
        api = TodoistAPI(secrets_path="nonexistent.json")
        with pytest.raises(TodoistAPIError) as exc_info:
            api._get_token()
        assert "Secrets file not found" in str(exc_info.value)

    @patch("builtins.open")
    @patch("pathlib.Path.exists")
    def test_raises_error_when_token_missing(self, mock_exists, mock_open):
        """Test that missing token raises TodoistAPIError."""
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = '{"other_key": "value"}'

        api = TodoistAPI()
        with pytest.raises(TodoistAPIError) as exc_info:
            api._get_token()
        assert "todoist_api_token not found" in str(exc_info.value)

    @patch("builtins.open")
    @patch("pathlib.Path.exists")
    def test_loads_token_successfully(self, mock_exists, mock_open):
        """Test successful token loading."""
        mock_exists.return_value = True
        mock_file = MagicMock()
        mock_file.read.return_value = '{"todoist_api_token": "test_token"}'
        mock_open.return_value.__enter__.return_value = mock_file

        api = TodoistAPI()
        token = api._get_token()

        assert token == "test_token"

    @patch("builtins.open")
    @patch("pathlib.Path.exists")
    def test_caches_token(self, mock_exists, mock_open):
        """Test that token is cached after first load."""
        mock_exists.return_value = True
        mock_file = MagicMock()
        mock_file.read.return_value = '{"todoist_api_token": "test_token"}'
        mock_open.return_value.__enter__.return_value = mock_file

        api = TodoistAPI()
        token1 = api._get_token()
        token2 = api._get_token()

        assert token1 == token2
        # File should only be opened once
        mock_open.assert_called_once()


class TestTodoistAPIGetTasks:
    """Test suite for TodoistAPI.get_tasks method."""

    @patch("apis.todoist.requests.get")
    @patch.object(TodoistAPI, "_get_token")
    def test_get_tasks_returns_formatted_tasks(self, mock_get_token, mock_requests_get):
        """Test get_tasks returns properly formatted tasks."""
        mock_get_token.return_value = "test_token"

        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "id": "task1",
                "content": "Buy groceries",
                "description": "Milk, eggs, bread",
                "priority": 2,
                "project_id": "project1",
                "labels": ["shopping"],
                "due": {
                    "date": "2025-01-15",
                    "datetime": None,
                    "string": "today",
                    "is_recurring": False,
                },
            }
        ]
        mock_requests_get.return_value = mock_response

        api = TodoistAPI()
        tasks = api.get_tasks("2025-01-15")

        assert len(tasks) == 1
        assert tasks[0]["id"] == "task1"
        assert tasks[0]["content"] == "Buy groceries"
        assert tasks[0]["description"] == "Milk, eggs, bread"
        assert tasks[0]["priority"] == 2
        assert tasks[0]["labels"] == ["shopping"]
        assert tasks[0]["due"]["date"] == "2025-01-15"

    @patch("apis.todoist.requests.get")
    @patch.object(TodoistAPI, "_get_token")
    def test_get_tasks_with_date_filter(self, mock_get_token, mock_requests_get):
        """Test get_tasks uses filter parameter for date."""
        mock_get_token.return_value = "test_token"

        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_requests_get.return_value = mock_response

        api = TodoistAPI()
        api.get_tasks("2025-01-15")

        mock_requests_get.assert_called_once()
        call_kwargs = mock_requests_get.call_args.kwargs
        assert call_kwargs["params"] == {"filter": "due: 2025-01-15"}
        assert "Authorization" in call_kwargs["headers"]

    @patch("apis.todoist.requests.get")
    @patch.object(TodoistAPI, "_get_token")
    def test_get_tasks_without_date(self, mock_get_token, mock_requests_get):
        """Test get_tasks without date returns all tasks."""
        mock_get_token.return_value = "test_token"

        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_requests_get.return_value = mock_response

        api = TodoistAPI()
        api.get_tasks()

        mock_requests_get.assert_called_once()
        call_kwargs = mock_requests_get.call_args.kwargs
        assert call_kwargs["params"] == {}

    @patch("apis.todoist.requests.get")
    @patch.object(TodoistAPI, "_get_token")
    def test_get_tasks_handles_no_due_date(self, mock_get_token, mock_requests_get):
        """Test get_tasks handles tasks without due date."""
        mock_get_token.return_value = "test_token"

        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "id": "task1",
                "content": "General task",
                "description": "",
                "priority": 1,
                "project_id": "project1",
                "labels": [],
                "due": None,
            }
        ]
        mock_requests_get.return_value = mock_response

        api = TodoistAPI()
        tasks = api.get_tasks()

        assert tasks[0]["due"] is None


class TestTodoistAPIFormatTask:
    """Test suite for TodoistAPI._format_task method."""

    def test_format_task_with_due_date(self):
        """Test formatting a task with due date."""
        api = TodoistAPI()

        raw_task = {
            "id": "123",
            "content": "Task title",
            "description": "Task description",
            "priority": 3,
            "project_id": "project123",
            "labels": ["work", "urgent"],
            "due": {
                "date": "2025-01-15",
                "datetime": "2025-01-15T10:00:00",
                "string": "Jan 15 10am",
                "is_recurring": False,
            },
        }

        formatted = api._format_task(raw_task)

        assert formatted["id"] == "123"
        assert formatted["content"] == "Task title"
        assert formatted["description"] == "Task description"
        assert formatted["priority"] == 3
        assert formatted["project_id"] == "project123"
        assert formatted["labels"] == ["work", "urgent"]
        assert formatted["due"]["date"] == "2025-01-15"
        assert formatted["due"]["datetime"] == "2025-01-15T10:00:00"
        assert formatted["due"]["string"] == "Jan 15 10am"
        assert formatted["due"]["is_recurring"] is False

    def test_format_task_without_due_date(self):
        """Test formatting a task without due date."""
        api = TodoistAPI()

        raw_task = {
            "id": "456",
            "content": "No due date task",
            "description": "",
            "priority": 1,
            "project_id": "project456",
            "labels": [],
            "due": None,
        }

        formatted = api._format_task(raw_task)

        assert formatted["due"] is None
