"""Calendar type classification module.

Classifies calendars into categories based on name patterns,
with support for config-based overrides.
"""

from __future__ import annotations

import json
import logging
import re
from enum import Enum


class CalendarType(Enum):
    """Calendar type categories."""

    BIRTHDAYS = "birthdays"  # Birthday reminders
    SOCIAL = "social"  # Food, drinks, meetings with friends
    WORK = "work"  # Work meetings, deadlines
    PERSONAL = "personal"  # Personal appointments
    RECURRING = "recurring"  # Recurring events (bills, chores)
    UNKNOWN = "unknown"  # Fallback


# Regex patterns for calendar name matching (case-insensitive)
CALENDAR_PATTERNS: dict[CalendarType, re.Pattern] = {
    CalendarType.BIRTHDAYS: re.compile(
        r"\b(birthday|birthdays|bday|bdays)\b",
        re.IGNORECASE,
    ),
    CalendarType.SOCIAL: re.compile(
        r"\b(food|drinks|social|friends|hangout|hangouts|lunch|dinner|coffee|brunch)\b",
        re.IGNORECASE,
    ),
    CalendarType.WORK: re.compile(
        r"\b(work|office|meetings|job|business|professional)\b",
        re.IGNORECASE,
    ),
    CalendarType.PERSONAL: re.compile(
        r"\b(personal|private|me|self|my)\b",
        re.IGNORECASE,
    ),
    CalendarType.RECURRING: re.compile(
        r"\b(bills|recurring|subscriptions|chores|routine|reminders)\b",
        re.IGNORECASE,
    ),
}

logger = logging.getLogger(__name__)


def _load_overrides() -> dict[str, CalendarType]:
    """Load calendar type overrides from config.

    Reads calendar_type_overrides from settings (via .env or env var).
    Format: {"Calendar Name": "type", ...}

    Returns:
        Dict mapping calendar names to CalendarType.
    """
    # Import here to avoid circular imports
    from jarvis.config import settings

    overrides_json = settings.calendar_type_overrides
    if not overrides_json:
        return {}

    try:
        raw = json.loads(overrides_json)
        result = {}
        for name, type_str in raw.items():
            try:
                result[name.lower()] = CalendarType(type_str)
            except ValueError:
                logger.warning(f"Invalid calendar type '{type_str}' for '{name}'")
        return result
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse CALENDAR_TYPE_OVERRIDES: {e}")
        return {}


def classify_calendar(name: str) -> CalendarType:
    """Classify a calendar by its name.

    Classification priority:
    1. Config override (CALENDAR_TYPE_OVERRIDES env var)
    2. Pattern matching on calendar name

    Args:
        name: The calendar name (e.g., "Birthdays", "Food", "Work").

    Returns:
        The detected CalendarType.
    """
    name_lower = name.lower()

    # Check config overrides first
    overrides = _load_overrides()
    if name_lower in overrides:
        logger.debug(f"Calendar '{name}' → {overrides[name_lower].value} (override)")
        return overrides[name_lower]

    # Pattern matching
    for cal_type, pattern in CALENDAR_PATTERNS.items():
        if pattern.search(name):
            logger.debug(f"Calendar '{name}' → {cal_type.value} (pattern)")
            return cal_type

    logger.debug(f"Calendar '{name}' → unknown")
    return CalendarType.UNKNOWN


def get_calendar_types(calendar_names: list[str]) -> dict[str, CalendarType]:
    """Classify multiple calendars at once.

    Args:
        calendar_names: List of calendar names.

    Returns:
        Dict mapping calendar name to CalendarType.
    """
    return {name: classify_calendar(name) for name in calendar_names}
