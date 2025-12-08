"""Tests for the Cache module."""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from cache import Cache, CacheEntry


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

    def test_default_ttl_config(self):
        """Test Cache has default TTL config."""
        cache = Cache()
        assert cache._ttl["weather"] == 1800
        assert cache._ttl["events"] == 300
        assert cache._ttl["todos"] == 300

    def test_custom_ttl_config(self):
        """Test Cache accepts custom TTL config."""
        cache = Cache(ttl_config={"weather": 60})
        assert cache._ttl["weather"] == 60
        # Others should still have defaults
        assert cache._ttl["events"] == 300


class TestCacheGet:
    """Test suite for Cache.get method."""

    @pytest.mark.asyncio
    async def test_fetches_on_miss(self):
        """Test cache fetches data on cache miss."""
        cache = Cache()
        fetcher = AsyncMock(return_value={"temp": 72})

        result = await cache.get("weather", fetcher)

        assert result == {"temp": 72}
        fetcher.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_cached_on_hit(self):
        """Test cache returns cached data on hit."""
        cache = Cache()
        fetcher = AsyncMock(return_value={"temp": 72})

        # First call fetches
        await cache.get("weather", fetcher)
        # Second call should use cache
        result = await cache.get("weather", fetcher)

        assert result == {"temp": 72}
        # Fetcher should only be called once
        fetcher.assert_called_once()

    @pytest.mark.asyncio
    async def test_force_refresh_bypasses_cache(self):
        """Test force_refresh fetches fresh data."""
        cache = Cache()
        fetcher = AsyncMock(side_effect=[{"temp": 72}, {"temp": 75}])

        # First call
        await cache.get("weather", fetcher)
        # Force refresh
        result = await cache.get("weather", fetcher, force_refresh=True)

        assert result == {"temp": 75}
        assert fetcher.call_count == 2

    @pytest.mark.asyncio
    async def test_refetches_on_expiry(self):
        """Test cache refetches when expired."""
        cache = Cache(ttl_config={"weather": 0})  # Instant expiry
        fetcher = AsyncMock(side_effect=[{"temp": 72}, {"temp": 75}])

        await cache.get("weather", fetcher)
        # Small delay to ensure expiry
        await asyncio.sleep(0.01)
        result = await cache.get("weather", fetcher)

        assert result == {"temp": 75}
        assert fetcher.call_count == 2


class TestCacheGetSync:
    """Test suite for Cache.get_sync method."""

    def test_returns_none_on_miss(self):
        """Test get_sync returns None on cache miss."""
        cache = Cache()
        assert cache.get_sync("weather") is None

    def test_returns_data_on_hit(self):
        """Test get_sync returns data on cache hit."""
        cache = Cache()
        cache.set("weather", {"temp": 72})

        assert cache.get_sync("weather") == {"temp": 72}

    def test_returns_none_on_expired(self):
        """Test get_sync returns None for expired entries."""
        cache = Cache()
        cache._cache["weather"] = CacheEntry(
            data={"temp": 72},
            expires_at=datetime.now() - timedelta(minutes=1),
        )

        assert cache.get_sync("weather") is None


class TestCacheSet:
    """Test suite for Cache.set method."""

    def test_set_stores_data(self):
        """Test set stores data in cache."""
        cache = Cache()
        cache.set("weather", {"temp": 72})

        assert cache.get_sync("weather") == {"temp": 72}

    def test_set_with_custom_ttl(self):
        """Test set with custom TTL."""
        cache = Cache()
        cache.set("custom", "data", ttl_seconds=60)

        entry = cache._cache["custom"]
        expected_expiry = datetime.now() + timedelta(seconds=60)
        # Allow 1 second tolerance
        assert abs((entry.expires_at - expected_expiry).total_seconds()) < 1


class TestCacheInvalidate:
    """Test suite for Cache.invalidate method."""

    def test_invalidate_removes_entry(self):
        """Test invalidate removes cache entry."""
        cache = Cache()
        cache.set("weather", {"temp": 72})

        result = cache.invalidate("weather")

        assert result is True
        assert cache.get_sync("weather") is None

    def test_invalidate_returns_false_on_miss(self):
        """Test invalidate returns False for missing key."""
        cache = Cache()
        assert cache.invalidate("nonexistent") is False


class TestCacheClear:
    """Test suite for Cache.clear method."""

    def test_clear_removes_all(self):
        """Test clear removes all entries."""
        cache = Cache()
        cache.set("weather", {"temp": 72})
        cache.set("events", [{"title": "Meeting"}])

        count = cache.clear()

        assert count == 2
        assert cache.get_sync("weather") is None
        assert cache.get_sync("events") is None


class TestCacheContextSummary:
    """Test suite for Cache.get_context_summary method."""

    def test_empty_when_no_data(self):
        """Test returns empty string when no cached data."""
        cache = Cache()
        assert cache.get_context_summary() == ""

    def test_includes_cached_data(self):
        """Test includes all cached data types."""
        cache = Cache()
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

    def test_returns_status_info(self):
        """Test get_status returns cache info."""
        cache = Cache()
        cache.set("weather", {"temp": 72})

        status = cache.get_status()

        assert "weather" in status
        assert "fetched_at" in status["weather"]
        assert "expires_at" in status["weather"]
        assert "is_expired" in status["weather"]
        assert "ttl_remaining" in status["weather"]
