"""Cache module for API data with TTL-based expiration and SQLite persistence.

This module provides caching for weather, events, and todos with:
- SQLite persistence (survives server restarts)
- TTL-based expiration
- Failure-tolerant fallback to stale data
"""

from __future__ import annotations

import json
import logging
import sqlite3
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
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
    """TTL-based cache with SQLite persistence.

    Provides async caching with:
    - Configurable TTLs per key type
    - SQLite persistence across restarts
    - Fallback to stale data on API failure

    Attributes:
        db_path: Path to the SQLite database.
        logger: Module logger instance.
    """

    DEFAULT_DB_PATH = "db/jarvis.db"

    # Default TTL values in seconds
    TTL_CONFIG: dict[str, int] = {
        "weather": 1800,  # 30 minutes
        "events": 300,  # 5 minutes
        "todos": 300,  # 5 minutes
    }

    def __init__(
        self,
        db_path: str | None = None,
        ttl_config: dict[str, int] | None = None,
    ) -> None:
        """Initialize the cache.

        Args:
            db_path: Path to SQLite database. Defaults to db/jarvis.db.
            ttl_config: Optional custom TTL configuration.
        """
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self.logger = logging.getLogger(__name__)
        self._memory_cache: dict[str, CacheEntry] = {}
        self._ttl = {**self.TTL_CONFIG, **(ttl_config or {})}
        self._ensure_db_exists()
        self._load_from_db()

    def _ensure_db_exists(self) -> None:
        """Ensure database and cache table exist."""
        db_file = Path(self.db_path)
        if not db_file.exists():
            from db.init import init_database

            init_database(self.db_path)
        else:
            # Ensure cache table exists (for existing DBs)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL
                )
            """)
            conn.commit()
            conn.close()

    def _load_from_db(self) -> None:
        """Load cached entries from database on startup."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT key, data, fetched_at, expires_at FROM cache_entries")
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            try:
                data = json.loads(row["data"])
                fetched_at = datetime.fromisoformat(row["fetched_at"])
                expires_at = datetime.fromisoformat(row["expires_at"])

                self._memory_cache[row["key"]] = CacheEntry(
                    data=data,
                    fetched_at=fetched_at,
                    expires_at=expires_at,
                )
                self.logger.debug(f"Loaded cache from db: {row['key']}")
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.warning(f"Failed to load cache entry {row['key']}: {e}")

    def _save_to_db(self, key: str, entry: CacheEntry) -> None:
        """Save a cache entry to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO cache_entries (key, data, fetched_at, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                key,
                json.dumps(entry.data, default=str),
                entry.fetched_at.isoformat(),
                entry.expires_at.isoformat(),
            ),
        )
        conn.commit()
        conn.close()
        self.logger.debug(f"Saved cache to db: {key}")

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

        On fetch failure, returns stale cached data if available (fallback).

        Args:
            key: Cache key (e.g., 'weather', 'events', 'todos').
            fetcher: Async function to fetch data if cache miss.
            force_refresh: If True, bypasses cache and fetches fresh data.

        Returns:
            The cached or freshly fetched data, or stale data on failure.
        """
        entry = self._memory_cache.get(key)

        # Return fresh cached data
        if not force_refresh and entry and not entry.is_expired:
            self.logger.debug(f"Cache hit: {key}")
            return entry.data

        # Try to fetch fresh data
        try:
            self.logger.info(f"Fetching fresh data for: {key}")
            data = await fetcher()

            # Store in memory and database
            ttl_seconds = self._get_ttl(key)
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
            new_entry = CacheEntry(data=data, expires_at=expires_at)

            self._memory_cache[key] = new_entry
            self._save_to_db(key, new_entry)

            self.logger.debug(f"Cached {key} (expires in {ttl_seconds}s)")
            return data

        except Exception as e:
            self.logger.error(f"Failed to fetch {key}: {e}")

            # Fallback to stale cached data if available
            if entry:
                self.logger.warning(f"Returning stale data for {key}")
                return entry.data

            # No fallback available
            self.logger.error(f"No fallback data for {key}")
            return None

    def get_sync(self, key: str, include_stale: bool = False) -> Any | None:
        """Get cached data synchronously without fetching.

        Args:
            key: Cache key.
            include_stale: If True, return stale data if no fresh data.

        Returns:
            Cached data if present (and optionally stale), else None.
        """
        entry = self._memory_cache.get(key)
        if entry and (not entry.is_expired or include_stale):
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
        entry = CacheEntry(data=data, expires_at=expires_at)

        self._memory_cache[key] = entry
        self._save_to_db(key, entry)
        self.logger.debug(f"Set cache: {key} (expires in {ttl}s)")

    def invalidate(self, key: str) -> bool:
        """Invalidate a specific cache entry.

        Args:
            key: Cache key to invalidate.

        Returns:
            True if key was present and removed, False otherwise.
        """
        removed = False
        if key in self._memory_cache:
            del self._memory_cache[key]
            removed = True

        # Also remove from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
        conn.commit()
        conn.close()

        if removed:
            self.logger.debug(f"Invalidated cache: {key}")
        return removed

    def clear(self) -> int:
        """Clear all cached data.

        Returns:
            Number of entries cleared.
        """
        count = len(self._memory_cache)
        self._memory_cache.clear()

        # Also clear database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cache_entries")
        conn.commit()
        conn.close()

        self.logger.info(f"Cleared {count} cache entries")
        return count

    def get_context_summary(self) -> str:
        """Generate a context summary of cached data for AI.

        Returns:
            A formatted string summarizing cached data.
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
        for key, entry in self._memory_cache.items():
            status[key] = {
                "fetched_at": entry.fetched_at.isoformat(),
                "expires_at": entry.expires_at.isoformat(),
                "is_expired": entry.is_expired,
                "ttl_remaining": max(0, (entry.expires_at - datetime.now()).total_seconds()),
            }
        return status

    # =========================================================================
    # Sliding Window Cache for Events
    # =========================================================================

    EVENTS_WINDOW_DAYS = 7  # Forward-looking cache window

    async def get_events_cached(
        self,
        start_date: date,  # noqa: F821
        end_date: date,  # noqa: F821
        fetcher: Callable[..., Awaitable[Any]],
        force_refresh: bool = False,
    ) -> list[dict[str, Any]]:
        """Get events with smart sliding window caching.

        For queries within the 7-day forward window, serves from a single cached
        window. For queries outside the window (historical or far-future), fetches
        directly without caching.

        Args:
            start_date: Start date of the query range.
            end_date: End date of the query range.
            fetcher: Async function to fetch events for a date range.
                     Should accept (start_date: str, end_date: str) args.
            force_refresh: If True, bypasses cache and fetches fresh data.

        Returns:
            List of event dictionaries matching the date range.
        """
        from datetime import date as date_type

        today = date_type.today()
        window_end = today + timedelta(days=self.EVENTS_WINDOW_DAYS - 1)

        # Check if query fits within the forward window
        if start_date >= today and end_date <= window_end:
            # Serve from window cache
            self.logger.debug(
                f"Events query {start_date} to {end_date} fits in window, using cache"
            )
            window_data = await self._get_or_refresh_events_window(fetcher, force_refresh)
            return self._filter_events_by_date_range(window_data, start_date, end_date)

        # Query is outside window - fetch directly without caching
        self.logger.info(
            f"Events query {start_date} to {end_date} outside window, fetching directly"
        )
        try:
            response = await fetcher(start_date.isoformat(), end_date.isoformat())
            if response and response.get("result"):
                import json as json_module

                return json_module.loads(response["result"])
            return []
        except Exception as e:
            self.logger.error(f"Failed to fetch events: {e}")
            return []

    async def _get_or_refresh_events_window(
        self,
        fetcher: Callable[..., Awaitable[Any]],
        force_refresh: bool = False,
    ) -> list[dict[str, Any]]:
        """Get or refresh the forward-looking events window cache.

        Args:
            fetcher: Async function to fetch events for a date range.
            force_refresh: If True, forces a refresh of the window.

        Returns:
            List of all events in the 7-day window.
        """
        from datetime import date as date_type

        cache_key = "events:window"

        async def fetch_window() -> dict[str, Any]:
            today = date_type.today()
            end = today + timedelta(days=self.EVENTS_WINDOW_DAYS - 1)
            return await fetcher(today.isoformat(), end.isoformat())

        result = await self.get(cache_key, fetch_window, force_refresh)

        if result and result.get("result"):
            import json as json_module

            return json_module.loads(result["result"])
        return []

    def _filter_events_by_date_range(
        self,
        events: list[dict[str, Any]],
        start_date: date,  # noqa: F821
        end_date: date,  # noqa: F821
    ) -> list[dict[str, Any]]:
        """Filter events to only include those within the date range.

        Args:
            events: List of event dictionaries with 'date' or 'start' fields.
            start_date: Start date of the range (inclusive).
            end_date: End date of the range (inclusive).

        Returns:
            Filtered list of events.
        """
        filtered = []
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()

        for event in events:
            # Get the event date from 'date' field or extract from 'start'
            event_date = event.get("date")
            if not event_date:
                start_field = event.get("start", "")
                event_date = start_field.split("T")[0] if "T" in start_field else start_field

            # Check if event falls within range
            if event_date and start_str <= event_date <= end_str:
                filtered.append(event)

        return filtered
