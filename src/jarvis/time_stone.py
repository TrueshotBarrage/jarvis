"""Time Stone - Temporal expression parser for natural language date range detection.

Named after the Infinity Stone that controls time in the Marvel Cinematic Universe,
this module allows Jarvis to understand and manipulate time-based queries.

Extracts date ranges from natural language queries like:
- "What events are upcoming this week?"
- "Any meetings tomorrow?"
- "What's on my calendar for the next 3 days?"

Uses a hybrid approach: regex for common patterns, LLM fallback for complex expressions.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jarvis.brain import Brain


class TemporalPattern(Enum):
    """Detected temporal pattern type."""

    TODAY = "today"
    TOMORROW = "tomorrow"
    YESTERDAY = "yesterday"
    THIS_WEEK = "this week"
    NEXT_WEEK = "next week"
    NEXT_N_DAYS = "next N days"
    SPECIFIC_WEEKDAY = "specific weekday"
    NONE = "none"


@dataclass
class TimeRange:
    """Represents a date range extracted from natural language.

    Attributes:
        start: Start date of the range (inclusive).
        end: End date of the range (inclusive).
        description: Human-readable description (e.g., "tomorrow", "this week").
        pattern: The pattern type that matched.
    """

    start: date
    end: date
    description: str
    pattern: TemporalPattern = TemporalPattern.NONE

    @property
    def is_single_day(self) -> bool:
        """Check if this range represents a single day."""
        return self.start == self.end

    @property
    def days(self) -> int:
        """Number of days in the range (inclusive)."""
        return (self.end - self.start).days + 1

    @classmethod
    def today(cls) -> TimeRange:
        """Create a TimeRange for today."""
        d = date.today()
        return cls(start=d, end=d, description="today", pattern=TemporalPattern.TODAY)

    @classmethod
    def tomorrow(cls) -> TimeRange:
        """Create a TimeRange for tomorrow."""
        d = date.today() + timedelta(days=1)
        return cls(start=d, end=d, description="tomorrow", pattern=TemporalPattern.TOMORROW)

    @classmethod
    def this_week(cls) -> TimeRange:
        """Create a TimeRange for this week (Monday to Sunday)."""
        today = date.today()
        # Monday = 0, Sunday = 6
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        return cls(
            start=monday, end=sunday, description="this week", pattern=TemporalPattern.THIS_WEEK
        )

    @classmethod
    def next_week(cls) -> TimeRange:
        """Create a TimeRange for next week (Monday to Sunday)."""
        today = date.today()
        # Find next Monday
        days_until_monday = 7 - today.weekday()
        next_monday = today + timedelta(days=days_until_monday)
        next_sunday = next_monday + timedelta(days=6)
        return cls(
            start=next_monday,
            end=next_sunday,
            description="next week",
            pattern=TemporalPattern.NEXT_WEEK,
        )

    @classmethod
    def next_n_days(cls, n: int) -> TimeRange:
        """Create a TimeRange for the next N days starting today."""
        today = date.today()
        end = today + timedelta(days=n - 1)
        return cls(
            start=today,
            end=end,
            description=f"next {n} days",
            pattern=TemporalPattern.NEXT_N_DAYS,
        )


# Regex patterns for common temporal expressions
TEMPORAL_PATTERNS: dict[TemporalPattern, re.Pattern] = {
    TemporalPattern.TODAY: re.compile(r"\btoday\b", re.IGNORECASE),
    TemporalPattern.TOMORROW: re.compile(r"\btomorrow\b", re.IGNORECASE),
    TemporalPattern.YESTERDAY: re.compile(r"\byesterday\b", re.IGNORECASE),
    TemporalPattern.THIS_WEEK: re.compile(r"\bthis\s+week\b", re.IGNORECASE),
    TemporalPattern.NEXT_WEEK: re.compile(r"\bnext\s+week\b", re.IGNORECASE),
    TemporalPattern.NEXT_N_DAYS: re.compile(r"\bnext\s+(\d+)\s+days?\b", re.IGNORECASE),
}

# Weekday patterns
WEEKDAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
WEEKDAY_PATTERN = re.compile(
    r"\b(?:next\s+)?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", re.IGNORECASE
)


class TemporalParser:
    """Parser for extracting date ranges from natural language.

    Uses regex for common patterns with optional LLM fallback for complex cases.

    Attributes:
        brain: Optional Brain instance for LLM fallback.
        logger: Module logger instance.
    """

    def __init__(self, brain: Brain | None = None) -> None:
        """Initialize the temporal parser.

        Args:
            brain: Optional Brain instance for LLM-based parsing of complex expressions.
        """
        self.brain = brain
        self.logger = logging.getLogger(__name__)

    def parse(self, message: str, reference_date: date | None = None) -> TimeRange | None:
        """Parse a message to extract a time range.

        Args:
            message: The user's message to parse.
            reference_date: Optional reference date for relative expressions.
                Defaults to today.

        Returns:
            TimeRange if a temporal expression was found, None otherwise.
        """
        ref = reference_date or date.today()

        # Try regex patterns in order of specificity
        result = self._try_regex_patterns(message, ref)
        if result:
            self.logger.debug(f"Temporal parse [regex]: '{message[:50]}' → {result.description}")
            return result

        # Try weekday pattern
        result = self._try_weekday_pattern(message, ref)
        if result:
            self.logger.debug(f"Temporal parse [weekday]: '{message[:50]}' → {result.description}")
            return result

        # No temporal expression found
        self.logger.debug(f"Temporal parse: no pattern found in '{message[:50]}'")
        return None

    def _try_regex_patterns(self, message: str, ref: date) -> TimeRange | None:
        """Try to match regex patterns for common expressions."""
        # Check for "next N days" first (most specific)
        match = TEMPORAL_PATTERNS[TemporalPattern.NEXT_N_DAYS].search(message)
        if match:
            n = int(match.group(1))
            # Limit to reasonable range
            n = min(n, 30)
            end = ref + timedelta(days=n - 1)
            return TimeRange(
                start=ref,
                end=end,
                description=f"next {n} days",
                pattern=TemporalPattern.NEXT_N_DAYS,
            )

        # Check other patterns
        if TEMPORAL_PATTERNS[TemporalPattern.TOMORROW].search(message):
            tomorrow = ref + timedelta(days=1)
            return TimeRange(
                start=tomorrow,
                end=tomorrow,
                description="tomorrow",
                pattern=TemporalPattern.TOMORROW,
            )

        if TEMPORAL_PATTERNS[TemporalPattern.YESTERDAY].search(message):
            yesterday = ref - timedelta(days=1)
            return TimeRange(
                start=yesterday,
                end=yesterday,
                description="yesterday",
                pattern=TemporalPattern.YESTERDAY,
            )

        if TEMPORAL_PATTERNS[TemporalPattern.NEXT_WEEK].search(message):
            # Find next Monday
            days_until_monday = 7 - ref.weekday()
            next_monday = ref + timedelta(days=days_until_monday)
            next_sunday = next_monday + timedelta(days=6)
            return TimeRange(
                start=next_monday,
                end=next_sunday,
                description="next week",
                pattern=TemporalPattern.NEXT_WEEK,
            )

        if TEMPORAL_PATTERNS[TemporalPattern.THIS_WEEK].search(message):
            # Monday of this week to Sunday
            monday = ref - timedelta(days=ref.weekday())
            sunday = monday + timedelta(days=6)
            return TimeRange(
                start=monday,
                end=sunday,
                description="this week",
                pattern=TemporalPattern.THIS_WEEK,
            )

        if TEMPORAL_PATTERNS[TemporalPattern.TODAY].search(message):
            return TimeRange(
                start=ref,
                end=ref,
                description="today",
                pattern=TemporalPattern.TODAY,
            )

        return None

    def _try_weekday_pattern(self, message: str, ref: date) -> TimeRange | None:
        """Try to match a specific weekday like 'Monday' or 'next Friday'."""
        match = WEEKDAY_PATTERN.search(message)
        if not match:
            return None

        weekday_name = match.group(1).lower()
        target_weekday = WEEKDAY_NAMES.index(weekday_name)
        current_weekday = ref.weekday()

        # Check if "next" prefix is present
        has_next_prefix = "next" in match.group(0).lower()

        # Calculate days until target weekday
        if has_next_prefix:
            # "next Monday" always means the Monday of next week
            days_until = (target_weekday - current_weekday + 7) % 7
            if days_until == 0:
                days_until = 7
        else:
            # "Monday" means this week's Monday if not passed, otherwise next
            days_until = (target_weekday - current_weekday) % 7
            # If the day has passed this week, go to next week
            if days_until == 0 and target_weekday < current_weekday:
                days_until = 7

        target_date = ref + timedelta(days=days_until)
        return TimeRange(
            start=target_date,
            end=target_date,
            description=weekday_name.capitalize(),
            pattern=TemporalPattern.SPECIFIC_WEEKDAY,
        )


# Module-level convenience function
_default_parser: TemporalParser | None = None


def parse_time_range(message: str, reference_date: date | None = None) -> TimeRange | None:
    """Parse a message to extract a time range.

    This is a convenience function using a module-level parser instance.

    Args:
        message: The user's message to parse.
        reference_date: Optional reference date for relative expressions.

    Returns:
        TimeRange if a temporal expression was found, None otherwise.
    """
    global _default_parser
    if _default_parser is None:
        _default_parser = TemporalParser()
    return _default_parser.parse(message, reference_date)


def detect_temporal_intent(message: str) -> bool:
    """Quick check if a message contains temporal expressions.

    This is a fast path to avoid full parsing when not needed.

    Args:
        message: The user's message to check.

    Returns:
        True if the message likely contains temporal expressions.
    """
    # Check all patterns
    for pattern in TEMPORAL_PATTERNS.values():
        if pattern.search(message):
            return True

    # Check weekday pattern
    return bool(WEEKDAY_PATTERN.search(message))
