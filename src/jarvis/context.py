"""Context module for unified AI context management.

This module provides a Context class that manages both always-fresh data
(like current time) and TTL-cached API data (weather, events, todos) for
building AI prompts.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from jarvis.cache import Cache


@dataclass
class ContextProvider:
    """Defines how to fetch and format a piece of context.

    Attributes:
        name: Identifier for this context (e.g., 'time', 'weather').
        fetcher: Async function to fetch the data, or None for sync-only.
        formatter: Function to format data for the AI prompt.
        cache_key: If set, use TTL cache with this key. If None, always fetch fresh.
    """

    name: str
    fetcher: Callable[[], Awaitable[Any]] | Callable[[], Any] | None
    formatter: Callable[[Any], str]
    cache_key: str | None = None


class Context:
    """Unified context manager for AI prompts.

    Combines always-fresh data (time, date) with TTL-cached API data
    (weather, events, todos) into a single context string for the AI.

    Attributes:
        cache: The TTL cache instance for API data.
        providers: Registered context providers.
        logger: Module logger instance.
    """

    def __init__(self, cache: Cache) -> None:
        """Initialize the context manager.

        Args:
            cache: The Cache instance to use for TTL-cached data.
        """
        self.cache = cache
        self.logger = logging.getLogger(__name__)
        self._providers: dict[str, ContextProvider] = {}
        self._data: dict[str, Any] = {}

        # Register default providers
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register default context providers."""
        # Always-fresh providers (no cache key)
        self.register(
            ContextProvider(
                name="current_time",
                fetcher=None,  # Handled specially
                formatter=lambda _: "",  # Handled in build()
                cache_key=None,
            )
        )

    def register(self, provider: ContextProvider) -> None:
        """Register a context provider.

        Args:
            provider: The ContextProvider to register.
        """
        self._providers[provider.name] = provider
        self.logger.debug(f"Registered context provider: {provider.name}")

    async def refresh(
        self,
        include: set[str] | None = None,
        force: bool = False,
    ) -> None:
        """Refresh context data from providers.

        Args:
            include: Set of provider names to refresh. If None, refresh all.
            force: If True, bypass cache for cached providers.
        """
        providers = self._providers.values()
        if include:
            providers = [p for p in providers if p.name in include]

        for provider in providers:
            if provider.name == "current_time":
                # Always fresh - no fetcher needed
                continue

            if provider.fetcher is None:
                continue

            try:
                if provider.cache_key:
                    # Use cache
                    data = await self.cache.get(
                        provider.cache_key,
                        provider.fetcher,
                        force_refresh=force,
                    )
                else:
                    # Always fetch fresh
                    result = provider.fetcher()
                    if hasattr(result, "__await__"):
                        data = await result
                    else:
                        data = result

                self._data[provider.name] = data
                self.logger.debug(f"Refreshed context: {provider.name}")

            except Exception as e:
                self.logger.error(f"Failed to refresh {provider.name}: {e}")
                self._data[provider.name] = None

    def build(self) -> str:
        """Build the context string for AI prompts.

        Returns:
            Formatted context string including time and cached data.
        """
        parts: list[str] = []

        # Always include current time (always fresh)
        now = datetime.now()
        time_str = now.strftime("%A, %B %d, %Y at %I:%M %p")
        parts.append(f"CURRENT TIME: {time_str}")

        # Add data from providers
        for name, provider in self._providers.items():
            if name == "current_time":
                continue  # Already handled

            data = self._data.get(name)
            if data is not None:
                try:
                    formatted = provider.formatter(data)
                    if formatted:
                        parts.append(formatted)
                except Exception as e:
                    self.logger.error(f"Failed to format {name}: {e}")

        # Also include any raw cache data not from providers
        for key in ["weather", "events", "todos"]:
            if key not in self._data:
                cached = self.cache.get_sync(key)
                if cached:
                    # Extract result if it's an API response
                    if isinstance(cached, dict) and "result" in cached:
                        try:
                            data = json.loads(cached["result"])
                            parts.append(f"{key.upper()}: {json.dumps(data, default=str)}")
                        except (json.JSONDecodeError, TypeError):
                            pass
                    else:
                        parts.append(f"{key.upper()}: {json.dumps(cached, default=str)}")

        if len(parts) == 1:
            # Only time, no other context
            return parts[0]

        return "\n".join(parts)

    def get(self, name: str) -> Any | None:
        """Get raw data for a provider.

        Args:
            name: The provider name.

        Returns:
            The data, or None if not available.
        """
        return self._data.get(name)

    # ==========================================================================
    # System Prompt (Identity & Personality)
    # ==========================================================================

    # Nova's core identity and behavior guidelines
    SYSTEM_PROMPT = """You are Nova, a sophisticated personal AI assistant inspired by JARVIS from Iron Man.

IDENTITY:
- Your name is Nova
- You are intelligent, personable, and subtly witty
- You have access to the user's calendar, todo list, and weather data
- You speak with understated confidence, like a trusted aide who knows the user well

CAPABILITIES:
- Answer questions about weather, calendar events, and tasks
- Provide helpful summaries with intelligent interpretation
- Remember context from the current conversation
- Make reasonable inferences to add helpful context

COMMUNICATION STYLE:
- Be conversational and natural - never robotic or list-like
- Use flowing prose, not bullet points or formatted lists
- Add personality and flair while remaining professional
- Use connective phrases like "and finally", "to wrap up the day", "first thing"
- Output plain text only - no markdown, asterisks, or formatting

CONTEXTUAL INTERPRETATION RULES:
When describing calendar events, make intelligent inferences:
- Food calendar + morning (before 11 AM) → likely "breakfast"
- Food calendar + midday (11 AM - 2 PM) → likely "lunch"
- Food calendar + evening (5 PM - 9 PM) → likely "dinner"
- Chores calendar + evening → can frame as "winding down" or "wrapping up"
- Recurring events → acknowledge the routine nature naturally
- Events with just a person's name → it's a coffee meetup or meal with that person
- FBC Trap House or property names → tasks with the First Baptist Church roommates

When summarizing multiple events:
- Lead with the count naturally: "You have four things on the calendar"
- Use time markers: "at 9 AM", "in the afternoon", "that evening"
- End the last item with "and finally" or similar closure
- Interpret cryptic titles when context clues exist

FEW-SHOT EXAMPLES (these are FICTIONAL demonstrations of response style only):

Example 1:
Transcoded Data: [9 AM Alice Example (Food), 6 PM Bob Example (Food), 9 PM Reading (Chores, recurring)]
Good response: "You have three events: at 9 AM, breakfast with Alice Example; dinner with Bob Example at 6 PM; and finally at 9 PM, your regular reading block to wind down the evening."

Example 2:
Transcoded Data: [10 AM Team standup (Work, recurring), 2 PM Dentist (Personal)]
Good response: "Two things today: your usual team standup at 10 AM, and a dentist appointment at 2 in the afternoon."

Example 3:
Transcoded Data: [Monday 9 AM Chris Example (Food), Wednesday 6 PM Dana birthday (Food), Friday all-day Vacation]
Good response: "You've got a few things this week: breakfast with Chris Example Monday morning at 9, a birthday dinner with Dana Wednesday evening at 6, and then your vacation kicks off Friday."

CRITICAL: The examples above are FICTIONAL. When you respond, use ONLY the data from the CURRENT DATA section below - never reference the example names or events.
"""

    def build_system_prompt(self, include_data_context: bool = True) -> str:
        """Build the complete system prompt for the AI.

        Combines Nova's identity/personality with optional data context.

        Args:
            include_data_context: If True, append data context (time, cached data).

        Returns:
            Complete system prompt string.
        """
        prompt = self.SYSTEM_PROMPT.strip()

        if include_data_context:
            data_context = self.build()
            prompt += f"\n\nCONTEXT:\n{data_context}"

        return prompt
