"""Google Calendar API wrapper module.

This module provides a wrapper around the Google Calendar API
using service account authentication for server-to-server access.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from google.auth.exceptions import GoogleAuthError
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from jarvis.config import settings


class CalendarAPIError(Exception):
    """Exception raised for Calendar API errors."""

    pass


class CalendarAPI:
    """Google Calendar API wrapper using service account authentication.

    This class provides methods to interact with Google Calendar API,
    fetching events for specific dates. It uses a service account for
    authentication, which requires sharing the target calendar with
    the service account's email address.

    Attributes:
        logger: Module logger instance.
        calendar_id: The calendar ID to query.
    """

    SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

    def __init__(
        self,
        credentials_path: str | None = None,
        calendar_id: str | None = None,
        calendar_ids: list[str] | None = None,
    ) -> None:
        """Initialize the Calendar API client.

        Args:
            credentials_path: Path to the service account credentials JSON file.
                Defaults to config setting or "google_credentials.json".
            calendar_id: Single calendar ID to query (for backwards compatibility).
            calendar_ids: List of calendar IDs to query. If None, will try to use
                GOOGLE_CALENDAR_IDS env var (comma-separated).
        """
        self.logger = logging.getLogger(__name__)
        self.credentials_path = credentials_path or settings.google_credentials_path

        # Priority for single calendar: explicit param > config > env var
        self.calendar_id = (
            calendar_id or settings.google_calendar_id or os.environ.get("GOOGLE_CALENDAR_ID")
        )

        # Priority for multiple calendars: explicit param > env var
        if calendar_ids:
            self.calendar_ids = calendar_ids
        else:
            env_ids = os.environ.get("GOOGLE_CALENDAR_IDS", "")
            if env_ids:
                self.calendar_ids = [cid.strip() for cid in env_ids.split(",") if cid.strip()]
            elif self.calendar_id:
                # Fallback: use single calendar_id if no multi-calendar config
                self.calendar_ids = [self.calendar_id]
            else:
                self.calendar_ids = []

        self._service: Any | None = None

    def _get_service(self) -> Any:
        """Get or create the Calendar API service.

        Returns:
            The Google Calendar API service object.

        Raises:
            CalendarAPIError: If credentials file is missing or invalid.
        """
        if self._service is not None:
            return self._service

        creds_path = Path(self.credentials_path)
        if not creds_path.exists():
            raise CalendarAPIError(
                f"Credentials file not found: {self.credentials_path}. "
                "Please download your service account credentials from "
                "Google Cloud Console and save them to this path."
            )

        try:
            credentials = service_account.Credentials.from_service_account_file(
                str(creds_path), scopes=self.SCOPES
            )
            self._service = build("calendar", "v3", credentials=credentials)
            self.logger.info("Google Calendar API service initialized")
            return self._service
        except (GoogleAuthError, json.JSONDecodeError) as e:
            raise CalendarAPIError(f"Failed to initialize Calendar API: {e}") from e

    def get_events(self, date: str) -> list[dict[str, Any]]:
        """Fetch calendar events for a specific date.

        Args:
            date: The date to fetch events for, in ISO format (YYYY-MM-DD).

        Returns:
            A list of event dictionaries, each containing:
                - id: Event ID
                - summary: Event title
                - start: Start time (ISO format or date)
                - end: End time (ISO format or date)
                - location: Event location (if set)
                - description: Event description (if set)

        Raises:
            CalendarAPIError: If the API request fails.
        """
        try:
            service = self._get_service()

            # Auto-detect calendar ID if not set
            if not self.calendar_id:
                self.calendar_id = self._detect_calendar_id(service)

            # Parse the date and create time bounds for the full day
            # Use the date string directly to create proper RFC3339 timestamps
            time_min = f"{date}T00:00:00Z"
            time_max = f"{date}T23:59:59Z"

            self.logger.info(f"Fetching events for {date} from calendar {self.calendar_id}")

            events_result = (
                service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])
            self.logger.info(f"Found {len(events)} events for {date}")

            return [self._format_event(event) for event in events]

        except HttpError as e:
            raise CalendarAPIError(f"Calendar API request failed: {e}") from e

    def get_all_calendars(self) -> list[dict[str, str]]:
        """Get all calendars accessible to the service account.

        Returns:
            A list of calendar dictionaries, each containing:
                - id: Calendar ID (email or unique ID)
                - name: Calendar display name
        """
        try:
            service = self._get_service()
            calendar_list = service.calendarList().list().execute()
            calendars = calendar_list.get("items", [])

            result = []
            for cal in calendars:
                result.append(
                    {
                        "id": cal["id"],
                        "name": cal.get("summary", cal["id"]),
                    }
                )

            self.logger.info(f"Found {len(result)} accessible calendar(s)")
            return result

        except HttpError as e:
            raise CalendarAPIError(f"Failed to list calendars: {e}") from e

    def get_all_events(self, date: str) -> list[dict[str, Any]]:
        """Fetch events from ALL configured calendars for a specific date.

        Uses calendar IDs from GOOGLE_CALENDAR_IDS env var (comma-separated)
        or falls back to GOOGLE_CALENDAR_ID.

        Args:
            date: The date to fetch events for, in ISO format (YYYY-MM-DD).

        Returns:
            A list of event dictionaries, each containing:
                - id: Event ID
                - summary: Event title
                - start: Start time (ISO format or date)
                - end: End time (ISO format or date)
                - location: Event location (if set)
                - description: Event description (if set)
                - calendar: Calendar name (e.g., "Work", "Food", "Chores")

        Raises:
            CalendarAPIError: If the API request fails.
        """
        try:
            service = self._get_service()

            if not self.calendar_ids:
                raise CalendarAPIError(
                    "No calendars configured! Set GOOGLE_CALENDAR_IDS env var "
                    "(comma-separated) or GOOGLE_CALENDAR_ID."
                )

            time_min = f"{date}T00:00:00Z"
            time_max = f"{date}T23:59:59Z"

            all_events = []

            for cal_id in self.calendar_ids:
                # Get calendar name from the API
                try:
                    cal_info = service.calendars().get(calendarId=cal_id).execute()
                    cal_name = cal_info.get("summary", cal_id)
                except HttpError:
                    # If we can't get the name, use the ID
                    cal_name = cal_id.split("@")[0] if "@" in cal_id else cal_id

                self.logger.info(f"Fetching events from '{cal_name}' ({cal_id})")

                try:
                    events_result = (
                        service.events()
                        .list(
                            calendarId=cal_id,
                            timeMin=time_min,
                            timeMax=time_max,
                            singleEvents=True,
                            orderBy="startTime",
                        )
                        .execute()
                    )

                    events = events_result.get("items", [])
                    self.logger.info(f"  Found {len(events)} events in '{cal_name}'")

                    for event in events:
                        formatted = self._format_event(event, calendar_name=cal_name)
                        all_events.append(formatted)

                except HttpError as e:
                    self.logger.warning(f"Failed to fetch from '{cal_name}': {e}")
                    continue

            # Sort all events by start time
            all_events.sort(key=lambda e: e["start"])

            self.logger.info(
                f"Total: {len(all_events)} events across {len(self.calendar_ids)} calendars"
            )
            return all_events

        except HttpError as e:
            raise CalendarAPIError(f"Calendar API request failed: {e}") from e

    def _detect_calendar_id(self, service: Any) -> str:
        """Auto-detect the first available shared calendar.

        Args:
            service: The Google Calendar API service.

        Returns:
            The calendar ID of the first shared calendar found.

        Raises:
            CalendarAPIError: If no shared calendars are found.
        """
        self.logger.info("No calendar_id set, attempting to auto-detect...")

        try:
            calendar_list = service.calendarList().list().execute()
            calendars = calendar_list.get("items", [])

            if calendars:
                # Log all available calendars
                self.logger.info(f"Found {len(calendars)} accessible calendar(s):")
                for cal in calendars:
                    self.logger.info(f"  - {cal['id']} ({cal.get('summary', 'N/A')})")

                # Return the first one
                chosen = calendars[0]["id"]
                self.logger.info(f"Using calendar: {chosen}")
                return chosen
            else:
                raise CalendarAPIError(
                    "No calendars found! Please share a calendar with the service account: "
                    "jarvis-service-account@gen-lang-client-0581620208.iam.gserviceaccount.com "
                    "or set GOOGLE_CALENDAR_ID environment variable to your calendar email."
                )
        except HttpError as e:
            raise CalendarAPIError(f"Failed to list calendars: {e}") from e

    def _format_event(
        self, event: dict[str, Any], calendar_name: str | None = None
    ) -> dict[str, Any]:
        """Format a raw API event into a simplified structure.

        Args:
            event: Raw event data from the Calendar API.
            calendar_name: Optional name of the calendar this event belongs to.

        Returns:
            Simplified event dictionary.
        """
        # Handle all-day events (which use 'date') vs timed events (which use 'dateTime')
        start = event.get("start", {})
        end = event.get("end", {})

        result = {
            "id": event.get("id", ""),
            "summary": event.get("summary", "Untitled Event"),
            "start": start.get("dateTime") or start.get("date", ""),
            "end": end.get("dateTime") or end.get("date", ""),
            "location": event.get("location", ""),
            "description": event.get("description", ""),
        }

        if calendar_name:
            result["calendar"] = calendar_name

        return result

    def set_calendar_id(self, calendar_id: str) -> CalendarAPI:
        """Set the calendar ID to query.

        Args:
            calendar_id: The calendar ID (e.g., "primary" or "user@gmail.com").

        Returns:
            Self for method chaining.
        """
        self.calendar_id = calendar_id
        return self
