"""Tests for the Context module."""

import os
import tempfile
from datetime import datetime

import pytest

from cache import Cache
from context import Context, ContextProvider


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)


class TestContextInit:
    """Test suite for Context initialization."""

    def test_initializes_with_cache(self, temp_db):
        """Test Context initializes with a Cache instance."""
        cache = Cache(db_path=temp_db)
        ctx = Context(cache)
        assert ctx.cache is cache

    def test_registers_default_providers(self, temp_db):
        """Test Context registers default providers on init."""
        cache = Cache(db_path=temp_db)
        ctx = Context(cache)
        assert "current_time" in ctx._providers


class TestContextBuild:
    """Test suite for Context.build method."""

    def test_includes_current_time(self, temp_db):
        """Test build includes current time."""
        cache = Cache(db_path=temp_db)
        ctx = Context(cache)

        result = ctx.build()

        assert "CURRENT TIME:" in result
        # Should have a reasonable date format
        assert datetime.now().strftime("%B") in result  # Month name

    def test_includes_cached_weather(self, temp_db):
        """Test build includes cached weather data."""
        cache = Cache(db_path=temp_db)
        cache.set("weather", {"result": '{"temp": 72}'})
        ctx = Context(cache)

        result = ctx.build()

        assert "WEATHER:" in result

    def test_includes_cached_events(self, temp_db):
        """Test build includes cached events data."""
        cache = Cache(db_path=temp_db)
        cache.set("events", {"result": '[{"title": "Meeting"}]'})
        ctx = Context(cache)

        result = ctx.build()

        assert "EVENTS:" in result

    def test_includes_cached_todos(self, temp_db):
        """Test build includes cached todos data."""
        cache = Cache(db_path=temp_db)
        cache.set("todos", {"result": '[{"task": "Buy milk"}]'})
        ctx = Context(cache)

        result = ctx.build()

        assert "TODOS:" in result


class TestContextProvider:
    """Test suite for ContextProvider dataclass."""

    def test_provider_creation(self):
        """Test creating a ContextProvider."""
        provider = ContextProvider(
            name="test",
            fetcher=None,
            formatter=lambda x: f"Test: {x}",
            cache_key=None,
        )

        assert provider.name == "test"
        assert provider.cache_key is None


class TestContextRegister:
    """Test suite for Context.register method."""

    def test_register_provider(self, temp_db):
        """Test registering a custom provider."""
        cache = Cache(db_path=temp_db)
        ctx = Context(cache)

        provider = ContextProvider(
            name="custom",
            fetcher=None,
            formatter=lambda x: f"Custom: {x}",
        )
        ctx.register(provider)

        assert "custom" in ctx._providers


class TestContextGet:
    """Test suite for Context.get method."""

    def test_get_returns_none_when_not_set(self, temp_db):
        """Test get returns None for missing data."""
        cache = Cache(db_path=temp_db)
        ctx = Context(cache)

        assert ctx.get("nonexistent") is None


class TestContextBuildSystemPrompt:
    """Test suite for Context.build_system_prompt method."""

    def test_includes_identity(self, temp_db):
        """Test build_system_prompt includes Nova's identity."""
        cache = Cache(db_path=temp_db)
        ctx = Context(cache)

        result = ctx.build_system_prompt()

        assert "Nova" in result
        assert "IDENTITY" in result

    def test_includes_capabilities(self, temp_db):
        """Test build_system_prompt includes capabilities."""
        cache = Cache(db_path=temp_db)
        ctx = Context(cache)

        result = ctx.build_system_prompt()

        assert "CAPABILITIES" in result

    def test_includes_data_context_by_default(self, temp_db):
        """Test build_system_prompt includes data context by default."""
        cache = Cache(db_path=temp_db)
        ctx = Context(cache)

        result = ctx.build_system_prompt()

        assert "CONTEXT:" in result
        assert "CURRENT TIME:" in result

    def test_excludes_data_context_when_disabled(self, temp_db):
        """Test build_system_prompt can exclude data context."""
        cache = Cache(db_path=temp_db)
        ctx = Context(cache)

        result = ctx.build_system_prompt(include_data_context=False)

        assert "CONTEXT:" not in result
        assert "CURRENT TIME:" not in result
