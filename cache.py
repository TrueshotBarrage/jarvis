"""Cache module for API data with TTL-based expiration.

This module provides in-memory caching for weather, events, and todos
with configurable time-to-live and force refresh capability.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


@dataclass
class CacheEntry:
    """A cached data entry with expiration tracking."""

    data: Any
    expires_at: datetime
    fetched_at: datetime = field(default_factory=datetime.now)

    @property
    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        return datetime.now() >= self.expires_at


class Cache:
    """TTL-based cache for API data.

    Provides async caching with configurable TTLs per key type.
    Supports force refresh and generates context summaries for AI.

    Attributes:
        logger: Module logger instance.
    """

    # Default TTL values in seconds
    TTL_CONFIG: dict[str, int] = {
        "weather": 1800,  # 30 minutes
        "events": 300,  # 5 minutes
        "todos": 300,  # 5 minutes
    }

    def __init__(self, ttl_config: dict[str, int] | None = None) -> None:
        """Initialize the cache.

        Args:
            ttl_config: Optional custom TTL configuration.
                Keys are cache keys, values are TTL in seconds.
        """
        self.logger = logging.getLogger(__name__)
        self._cache: dict[str, CacheEntry] = {}
        self._ttl = {**self.TTL_CONFIG, **(ttl_config or {})}

    def _get_ttl(self, key: str) -> int:
        """Get TTL for a key, defaulting to 5 minutes."""
        return self._ttl.get(key, 300)

    async def get(
        self,
        key: str,
        fetcher: Callable[[], Awaitable[Any]],
        force_refresh: bool = False,
    ) -> Any:
        """Get cached data or fetch if expired/missing.

        Args:
            key: Cache key (e.g., 'weather', 'events', 'todos').
            fetcher: Async function to fetch data if cache miss.
            force_refresh: If True, bypasses cache and fetches fresh data.

        Returns:
            The cached or freshly fetched data.
        """
        # Check cache hit
        entry = self._cache.get(key)

        if not force_refresh and entry and not entry.is_expired:
            self.logger.debug(f"Cache hit: {key}")
            return entry.data

        # Cache miss or expired or forced refresh
        self.logger.info(f"Fetching fresh data for: {key}")
        data = await fetcher()

        # Store in cache
        ttl_seconds = self._get_ttl(key)
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

        self._cache[key] = CacheEntry(data=data, expires_at=expires_at)
        self.logger.debug(f"Cached {key} (expires in {ttl_seconds}s)")

        return data

    def get_sync(self, key: str) -> Any | None:
        """Get cached data synchronously without fetching.

        Args:
            key: Cache key.

        Returns:
            Cached data if present and not expired, else None.
        """
        entry = self._cache.get(key)
        if entry and not entry.is_expired:
            return entry.data
        return None

    def set(self, key: str, data: Any, ttl_seconds: int | None = None) -> None:
        """Manually set a cache entry.

        Args:
            key: Cache key.
            data: Data to cache.
            ttl_seconds: Optional custom TTL. Uses default if not provided.
        """
        ttl = ttl_seconds if ttl_seconds is not None else self._get_ttl(key)
        expires_at = datetime.now() + timedelta(seconds=ttl)

        self._cache[key] = CacheEntry(data=data, expires_at=expires_at)
        self.logger.debug(f"Set cache: {key} (expires in {ttl}s)")

    def invalidate(self, key: str) -> bool:
        """Invalidate a specific cache entry.

        Args:
            key: Cache key to invalidate.

        Returns:
            True if key was present and removed, False otherwise.
        """
        if key in self._cache:
            del self._cache[key]
            self.logger.debug(f"Invalidated cache: {key}")
            return True
        return False

    def clear(self) -> int:
        """Clear all cached data.

        Returns:
            Number of entries cleared.
        """
        count = len(self._cache)
        self._cache.clear()
        self.logger.info(f"Cleared {count} cache entries")
        return count

    def get_context_summary(self) -> str:
        """Generate a context summary of cached data for AI.

        Returns:
            A formatted string summarizing cached data, suitable
            for including in AI prompts.
        """
        parts: list[str] = []

        weather = self.get_sync("weather")
        if weather:
            parts.append(f"Current weather data: {weather}")

        events = self.get_sync("events")
        if events:
            parts.append(f"Today's calendar events: {events}")

        todos = self.get_sync("todos")
        if todos:
            parts.append(f"Today's todos: {todos}")

        if not parts:
            return ""

        return "CACHED CONTEXT:\n" + "\n".join(parts)

    def get_status(self) -> dict[str, dict[str, Any]]:
        """Get cache status for debugging.

        Returns:
            Dict with cache key info including expiration status.
        """
        status = {}
        for key, entry in self._cache.items():
            status[key] = {
                "fetched_at": entry.fetched_at.isoformat(),
                "expires_at": entry.expires_at.isoformat(),
                "is_expired": entry.is_expired,
                "ttl_remaining": max(0, (entry.expires_at - datetime.now()).total_seconds()),
            }
        return status
