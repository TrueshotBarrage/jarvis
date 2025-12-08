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
