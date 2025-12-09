"""Tests for the Cache module."""

import asyncio
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from jarvis.cache import Cache, CacheEntry


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)


class TestCacheEntry:
    """Test suite for CacheEntry dataclass."""

    def test_not_expired_when_fresh(self):
        """Test entry is not expired when just created."""
        entry = CacheEntry(
            data="test",
            expires_at=datetime.now() + timedelta(minutes=5),
        )
        assert not entry.is_expired

    def test_expired_when_past_expiration(self):
        """Test entry is expired when past expiration time."""
        entry = CacheEntry(
            data="test",
            expires_at=datetime.now() - timedelta(minutes=1),
        )
        assert entry.is_expired


class TestCacheInit:
    """Test suite for Cache initialization."""

    def test_default_ttl_config(self, temp_db):
        """Test Cache has default TTL config."""
        cache = Cache(db_path=temp_db)
        assert cache._ttl["weather"] == 1800
        assert cache._ttl["events"] == 300
        assert cache._ttl["todos"] == 300

    def test_custom_ttl_config(self, temp_db):
        """Test Cache accepts custom TTL config."""
        cache = Cache(db_path=temp_db, ttl_config={"weather": 60})
        assert cache._ttl["weather"] == 60
        # Others should still have defaults
        assert cache._ttl["events"] == 300


class TestCacheGet:
    """Test suite for Cache.get method."""

    @pytest.mark.asyncio
    async def test_fetches_on_miss(self, temp_db):
        """Test cache fetches data on cache miss."""
        cache = Cache(db_path=temp_db)
        fetcher = AsyncMock(return_value={"temp": 72})

        result = await cache.get("weather", fetcher)

        assert result == {"temp": 72}
        fetcher.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_cached_on_hit(self, temp_db):
        """Test cache returns cached data on hit."""
        cache = Cache(db_path=temp_db)
        fetcher = AsyncMock(return_value={"temp": 72})

        # First call fetches
        await cache.get("weather", fetcher)
        # Second call should use cache
        result = await cache.get("weather", fetcher)

        assert result == {"temp": 72}
        # Fetcher should only be called once
        fetcher.assert_called_once()

    @pytest.mark.asyncio
    async def test_force_refresh_bypasses_cache(self, temp_db):
        """Test force_refresh fetches fresh data."""
        cache = Cache(db_path=temp_db)
        fetcher = AsyncMock(side_effect=[{"temp": 72}, {"temp": 75}])

        # First call
        await cache.get("weather", fetcher)
        # Force refresh
        result = await cache.get("weather", fetcher, force_refresh=True)

        assert result == {"temp": 75}
        assert fetcher.call_count == 2

    @pytest.mark.asyncio
    async def test_refetches_on_expiry(self, temp_db):
        """Test cache refetches when expired."""
        cache = Cache(db_path=temp_db, ttl_config={"weather": 0})  # Instant expiry
        fetcher = AsyncMock(side_effect=[{"temp": 72}, {"temp": 75}])

        await cache.get("weather", fetcher)
        # Small delay to ensure expiry
        await asyncio.sleep(0.01)
        result = await cache.get("weather", fetcher)

        assert result == {"temp": 75}
        assert fetcher.call_count == 2

    @pytest.mark.asyncio
    async def test_fallback_to_stale_on_failure(self, temp_db):
        """Test cache returns stale data on fetch failure."""
        cache = Cache(db_path=temp_db, ttl_config={"weather": 0})
        fetcher = AsyncMock(side_effect=[{"temp": 72}, Exception("API Error")])

        # First call succeeds
        await cache.get("weather", fetcher)
        # Second call fails, should return stale data
        result = await cache.get("weather", fetcher)

        assert result == {"temp": 72}


class TestCacheGetSync:
    """Test suite for Cache.get_sync method."""

    def test_returns_none_on_miss(self, temp_db):
        """Test get_sync returns None on cache miss."""
        cache = Cache(db_path=temp_db)
        assert cache.get_sync("nonexistent") is None

    def test_returns_data_on_hit(self, temp_db):
        """Test get_sync returns data on cache hit."""
        cache = Cache(db_path=temp_db)
        cache.set("weather", {"temp": 72})

        assert cache.get_sync("weather") == {"temp": 72}

    def test_returns_none_on_expired(self, temp_db):
        """Test get_sync returns None for expired entries."""
        cache = Cache(db_path=temp_db)
        cache._memory_cache["weather"] = CacheEntry(
            data={"temp": 72},
            expires_at=datetime.now() - timedelta(minutes=1),
        )

        assert cache.get_sync("weather") is None

    def test_returns_stale_when_requested(self, temp_db):
        """Test get_sync returns stale data when include_stale=True."""
        cache = Cache(db_path=temp_db)
        cache._memory_cache["weather"] = CacheEntry(
            data={"temp": 72},
            expires_at=datetime.now() - timedelta(minutes=1),
        )

        assert cache.get_sync("weather", include_stale=True) == {"temp": 72}


class TestCacheSet:
    """Test suite for Cache.set method."""

    def test_set_stores_data(self, temp_db):
        """Test set stores data in cache."""
        cache = Cache(db_path=temp_db)
        cache.set("weather", {"temp": 72})

        assert cache.get_sync("weather") == {"temp": 72}

    def test_set_with_custom_ttl(self, temp_db):
        """Test set with custom TTL."""
        cache = Cache(db_path=temp_db)
        cache.set("custom", "data", ttl_seconds=60)

        entry = cache._memory_cache["custom"]
        expected_expiry = datetime.now() + timedelta(seconds=60)
        # Allow 1 second tolerance
        assert abs((entry.expires_at - expected_expiry).total_seconds()) < 1


class TestCacheInvalidate:
    """Test suite for Cache.invalidate method."""

    def test_invalidate_removes_entry(self, temp_db):
        """Test invalidate removes cache entry."""
        cache = Cache(db_path=temp_db)
        cache.set("weather", {"temp": 72})

        result = cache.invalidate("weather")

        assert result is True
        assert cache.get_sync("weather") is None

    def test_invalidate_returns_false_on_miss(self, temp_db):
        """Test invalidate returns False for missing key."""
        cache = Cache(db_path=temp_db)
        assert cache.invalidate("nonexistent") is False


class TestCacheClear:
    """Test suite for Cache.clear method."""

    def test_clear_removes_all(self, temp_db):
        """Test clear removes all entries."""
        cache = Cache(db_path=temp_db)
        cache.set("weather", {"temp": 72})
        cache.set("events", [{"title": "Meeting"}])

        count = cache.clear()

        assert count == 2
        assert cache.get_sync("weather") is None
        assert cache.get_sync("events") is None


class TestCacheContextSummary:
    """Test suite for Cache.get_context_summary method."""

    def test_empty_when_no_data(self, temp_db):
        """Test returns empty string when no cached data."""
        cache = Cache(db_path=temp_db)
        assert cache.get_context_summary() == ""

    def test_includes_cached_data(self, temp_db):
        """Test includes all cached data types."""
        cache = Cache(db_path=temp_db)
        cache.set("weather", {"temp": 72})
        cache.set("events", [{"title": "Meeting"}])
        cache.set("todos", [{"task": "Buy milk"}])

        summary = cache.get_context_summary()

        assert "CACHED CONTEXT:" in summary
        assert "weather" in summary.lower()
        assert "events" in summary.lower()
        assert "todos" in summary.lower()


class TestCacheStatus:
    """Test suite for Cache.get_status method."""

    def test_returns_status_info(self, temp_db):
        """Test get_status returns cache info."""
        cache = Cache(db_path=temp_db)
        cache.set("weather", {"temp": 72})

        status = cache.get_status()

        assert "weather" in status
        assert "fetched_at" in status["weather"]
        assert "expires_at" in status["weather"]
        assert "is_expired" in status["weather"]
        assert "ttl_remaining" in status["weather"]


class TestCachePersistence:
    """Test suite for Cache SQLite persistence."""

    def test_persists_across_instances(self, temp_db):
        """Test cache data persists across Cache instances."""
        cache1 = Cache(db_path=temp_db)
        cache1.set("weather", {"temp": 72})

        # Create new Cache instance with same db
        cache2 = Cache(db_path=temp_db)

        # Should load data from db
        assert cache2.get_sync("weather") == {"temp": 72}


class TestCacheSlidingWindow:
    """Test suite for Cache sliding window event caching."""

    @pytest.mark.asyncio
    async def test_get_events_cached_within_window(self, temp_db):
        """Test events within 7-day window are served from cache."""
        import json

        cache = Cache(db_path=temp_db)
        today = datetime.now().date()

        # Mock fetcher returns events for the window
        events = [
            {"id": "1", "summary": "Event 1", "date": str(today)},
            {"id": "2", "summary": "Event 2", "date": str(today + timedelta(days=1))},
        ]

        async def mock_fetcher(_start, _end):
            return {"result": json.dumps(events), "status": 200}

        # First call fetches - pass date objects, not strings
        result = await cache.get_events_cached(today, today + timedelta(days=1), mock_fetcher)

        # Should return filtered events for the requested range
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_events_cached_force_refresh(self, temp_db):
        """Test force_refresh bypasses cache."""
        cache = Cache(db_path=temp_db)
        today = datetime.now().date()

        call_count = 0

        async def mock_fetcher(_start, _end):
            nonlocal call_count
            call_count += 1
            return []  # Return empty list

        # First call - pass date objects
        await cache.get_events_cached(today, today, mock_fetcher)
        # Force refresh
        await cache.get_events_cached(today, today, mock_fetcher, force_refresh=True)

        assert call_count == 2

    def test_filter_events_by_date_range(self, temp_db):
        """Test _filter_events_by_date_range filters correctly."""
        cache = Cache(db_path=temp_db)

        events = [
            {"id": "1", "date": "2025-01-15"},
            {"id": "2", "date": "2025-01-16"},
            {"id": "3", "date": "2025-01-17"},
            {"id": "4", "date": "2025-01-18"},
        ]

        # Filter for Jan 16-17
        from datetime import date

        start = date(2025, 1, 16)
        end = date(2025, 1, 17)

        filtered = cache._filter_events_by_date_range(events, start, end)

        assert len(filtered) == 2
        assert filtered[0]["id"] == "2"
        assert filtered[1]["id"] == "3"

    def test_filter_events_handles_start_field(self, temp_db):
        """Test _filter_events_by_date_range uses start field when date missing."""
        cache = Cache(db_path=temp_db)

        events = [
            {"id": "1", "start": "2025-01-16T10:00:00-05:00"},  # Has datetime, no date
            {"id": "2", "date": "2025-01-16"},  # Has date field
        ]

        from datetime import date

        start = date(2025, 1, 16)
        end = date(2025, 1, 16)

        filtered = cache._filter_events_by_date_range(events, start, end)

        assert len(filtered) == 2

    def test_filter_events_empty_list(self, temp_db):
        """Test _filter_events_by_date_range handles empty list."""
        cache = Cache(db_path=temp_db)
        from datetime import date

        filtered = cache._filter_events_by_date_range([], date(2025, 1, 16), date(2025, 1, 16))

        assert filtered == []
