"""Todoist REST API v2 wrapper module.

This module provides a wrapper around the Todoist REST API v2
using direct HTTP requests for fetching tasks.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests


class TodoistAPIError(Exception):
    """Exception raised for Todoist API errors."""

    pass


class TodoistAPI:
    """Todoist REST API v2 wrapper.

    This class provides methods to interact with the Todoist API,
    fetching tasks for specific dates using direct HTTP requests.

    Attributes:
        logger: Module logger instance.
    """

    DEFAULT_SECRETS_PATH = "secrets.json"
    BASE_URL = "https://api.todoist.com/rest/v2"

    def __init__(self, secrets_path: str | None = None) -> None:
        """Initialize the Todoist API client.

        Args:
            secrets_path: Path to the secrets JSON file containing the API token.
                Defaults to "secrets.json" in the project root.
        """
        self.logger = logging.getLogger(__name__)
        self.secrets_path = secrets_path or self.DEFAULT_SECRETS_PATH
        self._token: str | None = None

    def _get_token(self) -> str:
        """Get the API token from secrets file.

        Returns:
            The Todoist API token.

        Raises:
            TodoistAPIError: If secrets file is missing or token not found.
        """
        if self._token is not None:
            return self._token

        secrets_file = Path(self.secrets_path)
        if not secrets_file.exists():
            raise TodoistAPIError(
                f"Secrets file not found: {self.secrets_path}. "
                "Please create secrets.json with your todoist_api_token."
            )

        try:
            with open(secrets_file) as f:
                secrets = json.load(f)
        except json.JSONDecodeError as e:
            raise TodoistAPIError(f"Invalid JSON in secrets file: {e}") from e

        token = secrets.get("todoist_api_token")
        if not token:
            raise TodoistAPIError(
                "todoist_api_token not found in secrets.json. "
                "Get your token from Todoist Settings → Integrations → Developer."
            )

        self._token = token
        self.logger.info("Todoist API token loaded")
        return self._token

    def get_tasks(self, date: str | None = None) -> list[dict[str, Any]]:
        """Fetch tasks from Todoist, optionally filtered by due date.

        Args:
            date: Optional date string in ISO format (YYYY-MM-DD) to filter tasks.
                If provided, only tasks due on this date are returned.
                If None, returns all active tasks.

        Returns:
            A list of task dictionaries, each containing:
                - id: Task ID
                - content: Task title/content
                - description: Task description (if set)
                - due: Due date/time info (if set)
                - priority: Task priority (1-4, where 4 is highest)
                - project_id: ID of the project containing the task
                - labels: List of label names

        Raises:
            TodoistAPIError: If the API request fails.
        """
        try:
            token = self._get_token()
            headers = {"Authorization": f"Bearer {token}"}

            self.logger.info(f"Fetching tasks{f' for {date}' if date else ''}")

            # Use filter parameter for date if provided
            params = {}
            if date:
                params["filter"] = f"due: {date}"

            response = requests.get(
                f"{self.BASE_URL}/tasks",
                headers=headers,
                params=params,
                timeout=30,
            )
            response.raise_for_status()

            tasks = response.json()
            self.logger.info(f"Found {len(tasks)} task(s)")

            return [self._format_task(task) for task in tasks]

        except requests.exceptions.RequestException as e:
            raise TodoistAPIError(f"Todoist API request failed: {e}") from e

    def _format_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Format a raw API task into a simplified structure.

        Args:
            task: Raw task dict from the Todoist API.

        Returns:
            Simplified task dictionary.
        """
        result: dict[str, Any] = {
            "id": task.get("id", ""),
            "content": task.get("content", ""),
            "description": task.get("description", ""),
            "priority": task.get("priority", 1),
            "project_id": task.get("project_id", ""),
            "labels": task.get("labels", []),
        }

        # Handle due date if present
        due = task.get("due")
        if due:
            result["due"] = {
                "date": due.get("date"),
                "datetime": due.get("datetime"),
                "string": due.get("string"),
                "is_recurring": due.get("is_recurring", False),
            }
        else:
            result["due"] = None

        return result
