"""Todoist REST API v2 wrapper module.

This module provides a wrapper around the Todoist REST API v2
using direct HTTP requests for fetching tasks.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from jarvis.config import settings


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

    BASE_URL = "https://api.todoist.com/rest/v2"

    def __init__(self) -> None:
        """Initialize the Todoist API client."""
        self.logger = logging.getLogger(__name__)
        self._token: str | None = None

    def _get_token(self) -> str:
        """Get the API token from config.

        Returns:
            The Todoist API token.

        Raises:
            TodoistAPIError: If token not configured.
        """
        if self._token is not None:
            return self._token

        if not settings.todoist_api_token:
            raise TodoistAPIError(
                "TODOIST_API_TOKEN not configured. Set it in .env or as an environment variable."
            )

        self._token = settings.todoist_api_token
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
