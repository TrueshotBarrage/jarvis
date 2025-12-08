"""Arms module - HTTP client for external API communication.

This module provides async HTTP capabilities for reaching out to external
services like weather APIs, Todoist, and Google Calendar.
"""

import json
import logging
from typing import Any, TypedDict

import httpx

from apis.weather import WeatherAPI


class APIResponse(TypedDict):
    """Standard response format for API calls."""

    result: str | None
    status: int


class Arms:
    """Async HTTP client for external API communication.

    This class wraps httpx.AsyncClient and provides convenient methods
    for making API calls to various services.

    Attributes:
        logger: Module logger instance.
        client: The underlying httpx AsyncClient (None until started).
    """

    def __init__(self) -> None:
        """Initialize Arms with logging configured."""
        self.logger = logging.getLogger(__name__)
        self.client: httpx.AsyncClient | None = None
        self.logger.info(
            "Useful appendages fully functional and ready to grab things at your command!"
        )

    def __call__(self) -> httpx.AsyncClient:
        """Return the wrapped httpx client singleton.

        Returns:
            The active httpx AsyncClient.

        Raises:
            AssertionError: If client hasn't been started.
        """
        assert self.client is not None, "Client not started. Call start() first."
        self.logger.info(
            f"httpx client.is_closed(): {self.client.is_closed}. "
            f"ID (will be unchanged): {id(self.client)}"
        )
        return self.client

    def start(self) -> None:
        """Start the async HTTP client. Call from FastAPI startup hook."""
        self.client = httpx.AsyncClient()
        self.logger.info(f"httpx AsyncClient started. ID {id(self.client)}")

    async def stop(self) -> None:
        """Gracefully shut down the client. Call from FastAPI shutdown hook."""
        if self.client is None:
            return

        self.logger.info(
            f"httpx client.is_closed(): {self.client.is_closed} - "
            f"Now can be closed. ID (will be unchanged): {id(self.client)}"
        )
        await self.client.aclose()
        self.logger.info(
            f"httpx client.is_closed(): {self.client.is_closed}. "
            f"ID (will be unchanged): {id(self.client)}"
        )
        self.client = None
        self.logger.info("httpx AsyncClient closed.")

    async def get(self, url: str, params: dict[str, Any] | None = None) -> APIResponse:
        """Make an async GET request.

        Args:
            url: The URL to request.
            params: Optional query parameters.

        Returns:
            APIResponse with result text and status code.
        """
        res = None
        try:
            res = await self.client.get(url, params=params)
            res.raise_for_status()
        except httpx.HTTPError as e:
            self.logger.error(f"Error: {e}")
            return {"result": None, "status": res.status_code if res else 404}

        return {"result": res.text, "status": res.status_code}

    async def get_weather(self) -> APIResponse:
        """Fetch current weather from Open-Meteo API.

        Returns:
            APIResponse containing weather JSON data.
        """
        weather_api = WeatherAPI()
        weather_url = weather_api.build_url()
        return await self.get(weather_url)

    async def get_todos(self, day: str) -> APIResponse:
        """Fetch todos for a specific day from Todoist.

        Args:
            day: Date string in ISO format (YYYY-MM-DD) for which to fetch todos.

        Returns:
            APIResponse containing todos data as JSON.
        """
        try:
            from apis.todoist import TodoistAPI, TodoistAPIError

            todoist_api = TodoistAPI()
            tasks = todoist_api.get_tasks(day)
            return {"result": json.dumps(tasks), "status": 200}
        except TodoistAPIError as e:
            self.logger.error(f"Todoist API error: {e}")
            return {"result": None, "status": 500}

    async def get_events(self, day: str) -> APIResponse:
        """Fetch calendar events from ALL shared calendars for a specific day.

        Args:
            day: Date string in ISO format (YYYY-MM-DD) for which to fetch events.

        Returns:
            APIResponse containing calendar events data as JSON.
            Each event includes a 'calendar' field with the calendar name.
        """
        try:
            from apis.calendar import CalendarAPI, CalendarAPIError

            calendar_api = CalendarAPI()
            events = calendar_api.get_all_events(day)
            return {"result": json.dumps(events), "status": 200}
        except CalendarAPIError as e:
            self.logger.error(f"Calendar API error: {e}")
            return {"result": None, "status": 500}

    async def run_autobudget_pipeline(self) -> APIResponse:
        """Trigger the autobudget pipeline on external server.

        Returns:
            APIResponse from the pipeline execution.

        TODO:
            Set up server instance (cloud or RPi) with fixed endpoint.
        """
        # TODO: Set up a server instance (cloud or RPi and establish a fixed endpoint)
        endpoint_base = ""
        endpoint_run = f"{endpoint_base}/run"
        return await self.get(endpoint_run)
