"""Semantic Transcoder - Transforms raw API data into human-readable summaries.

This module handles the deterministic data transformation that the LLM struggles with,
converting raw JSON API responses into structured, human-readable text that requires
no date reasoning or JSON parsing from the language model.

The transcoder ensures consistency and reliability by handling:
- Date formatting and relative date labels (TODAY, TOMORROW)
- Time formatting (12-hour with AM/PM)
- Event grouping by date
- Priority indicators for tasks
- Weather condition summaries
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from jarvis.time_stone import TimeRange


@dataclass
class TranscoderConfig:
    """Configuration for the semantic transcoder.

    Attributes:
        use_emoji: Whether to include emoji in output.
        include_relative_dates: Whether to include TODAY/TOMORROW labels.
        time_format_24h: Whether to use 24-hour time format.
    """

    use_emoji: bool = True
    include_relative_dates: bool = True
    time_format_24h: bool = False


class SemanticTranscoder:
    """Transforms raw API responses into human-readable summaries.

    Handles all deterministic data transformation so the LLM can focus on
    natural language generation without reasoning about dates or parsing JSON.

    Attributes:
        config: Transcoder configuration options.
        logger: Module logger instance.
    """

    def __init__(self, config: TranscoderConfig | None = None) -> None:
        """Initialize the semantic transcoder.

        Args:
            config: Optional configuration. Uses defaults if not provided.
        """
        self.config = config or TranscoderConfig()
        self.logger = logging.getLogger(__name__)

    # =========================================================================
    # Date/Time Formatting
    # =========================================================================

    def format_date_full(self, date_input: str | date) -> str:
        """Format a date as 'Tuesday, December 9th, 2025'.

        Args:
            date_input: ISO date string (YYYY-MM-DD) or date object.

        Returns:
            Fully formatted date string.
        """
        if isinstance(date_input, str):
            d = datetime.strptime(date_input.split("T")[0], "%Y-%m-%d").date()
        else:
            d = date_input

        day_suffix = self._get_day_suffix(d.day)
        return d.strftime(f"%A, %B {d.day}{day_suffix}, %Y")

    def format_date_short(self, date_input: str | date) -> str:
        """Format a date as 'Dec 9'.

        Args:
            date_input: ISO date string or date object.

        Returns:
            Short formatted date string.
        """
        if isinstance(date_input, str):
            d = datetime.strptime(date_input.split("T")[0], "%Y-%m-%d").date()
        else:
            d = date_input

        return d.strftime(f"%b {d.day}")

    def format_time(self, datetime_input: str | datetime) -> str:
        """Format a datetime as '10:00 AM' or '14:00'.

        Args:
            datetime_input: ISO datetime string or datetime object.

        Returns:
            Formatted time string.
        """
        if isinstance(datetime_input, str):
            # Handle both datetime and date-only strings
            if "T" not in datetime_input:
                return "All day"
            dt = datetime.fromisoformat(datetime_input.replace("Z", "+00:00"))
        else:
            dt = datetime_input

        if self.config.time_format_24h:
            return dt.strftime("%H:%M")
        else:
            # 12-hour format without leading zero
            return dt.strftime("%I:%M %p").lstrip("0")

    def get_relative_date_label(self, date_input: str | date) -> str | None:
        """Get relative label like 'TODAY' or 'TOMORROW' if applicable.

        Args:
            date_input: ISO date string or date object.

        Returns:
            Relative label or None if not today/tomorrow.
        """
        if isinstance(date_input, str):
            d = datetime.strptime(date_input.split("T")[0], "%Y-%m-%d").date()
        else:
            d = date_input

        today = date.today()
        if d == today:
            return "TODAY"
        elif d == today.replace(day=today.day + 1) if today.day < 28 else None:
            # Safe day increment check
            from datetime import timedelta

            if d == today + timedelta(days=1):
                return "TOMORROW"
        else:
            from datetime import timedelta

            if d == today + timedelta(days=1):
                return "TOMORROW"

        return None

    def _get_day_suffix(self, day: int) -> str:
        """Get ordinal suffix for a day number (st, nd, rd, th)."""
        if 11 <= day <= 13:
            return "th"
        return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

    # =========================================================================
    # Weather Transcoding
    # =========================================================================

    def transcode_weather(self, weather_data: dict[str, Any]) -> str:
        """Transform weather API response into readable summary.

        Args:
            weather_data: Raw weather API response from Open-Meteo.

        Returns:
            Human-readable weather summary.
        """
        if not weather_data:
            return "Weather data unavailable."

        lines = []

        # Current conditions
        current = weather_data.get("current", {})
        units = weather_data.get("current_units", {})

        if current:
            temp = current.get("temperature_2m")
            precip = current.get("precipitation", 0)
            temp_unit = units.get("temperature_2m", "°F")

            lines.append("CURRENT WEATHER:")
            if temp is not None:
                lines.append(f"  Temperature: {temp:.0f}{temp_unit}")
            if precip > 0:
                lines.append(f"  Precipitation: {precip}mm")
            else:
                lines.append("  Precipitation: None")
            lines.append("")

        # Daily forecast
        daily = weather_data.get("daily", {})
        if daily and daily.get("time"):
            dates = daily.get("time", [])
            highs = daily.get("temperature_2m_max", [])
            lows = daily.get("temperature_2m_min", [])
            sunrises = daily.get("sunrise", [])
            sunsets = daily.get("sunset", [])

            for i, date_str in enumerate(dates[:3]):  # Max 3 days
                relative = self.get_relative_date_label(date_str)
                full_date = self.format_date_full(date_str)

                if relative and self.config.include_relative_dates:
                    lines.append(f"{relative}'S FORECAST ({full_date}):")
                else:
                    lines.append(f"FORECAST FOR {full_date}:")

                if i < len(highs) and i < len(lows):
                    lines.append(f"  High: {highs[i]:.0f}°F, Low: {lows[i]:.0f}°F")

                if i < len(sunrises) and i < len(sunsets):
                    sunrise_time = self.format_time(sunrises[i])
                    sunset_time = self.format_time(sunsets[i])
                    lines.append(f"  Sunrise: {sunrise_time}, Sunset: {sunset_time}")

                lines.append("")

        return "\n".join(lines).strip()

    # =========================================================================
    # Events Transcoding
    # =========================================================================

    def transcode_events(
        self,
        events: list[dict[str, Any]],
        time_range: TimeRange | None = None,
    ) -> str:
        """Transform calendar events into readable summary.

        Groups events by date and formats with clear time/location info.

        Args:
            events: List of event dictionaries from Calendar API.
            time_range: Optional TimeRange for context labeling.

        Returns:
            Human-readable events summary grouped by date.
        """
        if not events:
            range_desc = time_range.description if time_range else "the requested period"
            return f"No events scheduled for {range_desc}."

        # Group events by date
        events_by_date: dict[str, list[dict]] = {}
        for event in events:
            event_date = event.get("date") or event.get("start", "").split("T")[0]
            if event_date:
                if event_date not in events_by_date:
                    events_by_date[event_date] = []
                events_by_date[event_date].append(event)

        lines = []
        sorted_dates = sorted(events_by_date.keys())

        for date_str in sorted_dates:
            date_events = events_by_date[date_str]

            # Build date header
            relative = self.get_relative_date_label(date_str)
            full_date = self.format_date_full(date_str)

            if relative and self.config.include_relative_dates:
                header = f"EVENTS FOR {relative} ({full_date}):"
            else:
                header = f"EVENTS FOR {full_date}:"

            lines.append(header)
            lines.append("")

            # Format each event
            for event in sorted(date_events, key=lambda e: e.get("start", "")):
                event_line = self._format_single_event(event)
                lines.append(event_line)

            lines.append(f"  ({len(date_events)} event{'s' if len(date_events) != 1 else ''})")
            lines.append("")

        # Summary
        total = len(events)
        if time_range:
            lines.append(
                f"Total: {total} event{'s' if total != 1 else ''} for {time_range.description}"
            )

        return "\n".join(lines).strip()

    def _format_single_event(self, event: dict[str, Any]) -> str:
        """Format a single event into a readable line."""
        lines = []

        summary = event.get("summary", "Untitled Event")
        start = event.get("start", "")
        end = event.get("end", "")
        location = event.get("location", "")
        calendar = event.get("calendar", "")
        calendar_type = event.get("calendar_type", "")

        # Determine if all-day event
        is_all_day = "T" not in start

        # Build main line
        if is_all_day:
            # Check for birthday
            if calendar_type == "birthdays" or "birthday" in summary.lower():
                emoji = "🎂 " if self.config.use_emoji else ""
                main_line = f"  {emoji}{summary} (all day)"
            else:
                main_line = f"  {summary} (all day)"
        else:
            start_time = self.format_time(start)
            if end and "T" in end:
                end_time = self.format_time(end)
                main_line = f"  {start_time} - {end_time}: {summary}"
            else:
                main_line = f"  {start_time}: {summary}"

        lines.append(main_line)

        # Add location if present
        if location:
            loc_emoji = "📍 " if self.config.use_emoji else ""
            lines.append(f"    {loc_emoji}{location}")

        # Add calendar info
        if calendar:
            cal_emoji = "📅 " if self.config.use_emoji else ""
            lines.append(f"    {cal_emoji}{calendar} calendar")

        return "\n".join(lines)

    # =========================================================================
    # Todos Transcoding
    # =========================================================================

    def transcode_todos(self, todos: list[dict[str, Any]]) -> str:
        """Transform todo list into readable summary.

        Groups tasks by due date with priority indicators.

        Args:
            todos: List of todo dictionaries from Todoist API.

        Returns:
            Human-readable todo summary grouped by date.
        """
        if not todos:
            return "No tasks scheduled."

        # Group todos by due date
        todos_by_date: dict[str, list[dict]] = {}
        no_date_todos: list[dict] = []

        for todo in todos:
            due = todo.get("due", {})
            due_date = due.get("date") if due else None

            if due_date:
                if due_date not in todos_by_date:
                    todos_by_date[due_date] = []
                todos_by_date[due_date].append(todo)
            else:
                no_date_todos.append(todo)

        lines = []
        sorted_dates = sorted(todos_by_date.keys())

        for date_str in sorted_dates:
            date_todos = todos_by_date[date_str]

            # Build date header
            relative = self.get_relative_date_label(date_str)
            full_date = self.format_date_full(date_str)

            if relative and self.config.include_relative_dates:
                header = f"TASKS FOR {relative} ({full_date}):"
            else:
                header = f"TASKS FOR {full_date}:"

            lines.append(header)

            for todo in date_todos:
                todo_line = self._format_single_todo(todo)
                lines.append(todo_line)

            lines.append("")

        # Tasks without due date
        if no_date_todos:
            lines.append("TASKS (no due date):")
            for todo in no_date_todos:
                todo_line = self._format_single_todo(todo)
                lines.append(todo_line)
            lines.append("")

        # Summary
        total = len(todos)
        lines.append(f"Total: {total} task{'s' if total != 1 else ''}")

        return "\n".join(lines).strip()

    def _format_single_todo(self, todo: dict[str, Any]) -> str:
        """Format a single todo into a readable line."""
        content = todo.get("content", "Untitled task")
        priority = todo.get("priority", 1)

        # Priority indicators (Todoist: 4=highest, 1=lowest)
        priority_map = {
            4: "[!]",  # High priority
            3: "[-]",  # Medium priority
            2: "[ ]",  # Low priority
            1: "[ ]",  # No priority
        }
        indicator = priority_map.get(priority, "[ ]")

        line = f"  {indicator} {content}"

        # Add priority label for high/medium
        if priority == 4:
            line += " (high priority)"
        elif priority == 3:
            line += " (medium priority)"

        return line

    # =========================================================================
    # Combined Transcoding
    # =========================================================================

    def transcode_all(
        self,
        data: dict[str, Any],
        time_range: TimeRange | None = None,
    ) -> str:
        """Transcode all available data into a combined summary.

        Args:
            data: Dictionary with optional 'weather', 'events', 'todos' keys.
            time_range: Optional TimeRange for event context.

        Returns:
            Combined human-readable summary.
        """
        sections = []

        if "weather" in data:
            weather_text = self.transcode_weather(data["weather"])
            if weather_text:
                sections.append(weather_text)

        if "events" in data:
            events_text = self.transcode_events(data["events"], time_range)
            if events_text:
                sections.append(events_text)

        if "todos" in data:
            todos_text = self.transcode_todos(data["todos"])
            if todos_text:
                sections.append(todos_text)

        if not sections:
            return "No data available."

        return "\n\n---\n\n".join(sections)


# Module-level convenience instance
_default_transcoder: SemanticTranscoder | None = None


def get_transcoder() -> SemanticTranscoder:
    """Get the default transcoder instance."""
    global _default_transcoder
    if _default_transcoder is None:
        _default_transcoder = SemanticTranscoder()
    return _default_transcoder
