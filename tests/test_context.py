"""Tests for the Context module."""

from datetime import datetime

from cache import Cache
from context import Context, ContextProvider


class TestContextInit:
    """Test suite for Context initialization."""

    def test_initializes_with_cache(self):
        """Test Context initializes with a Cache instance."""
        cache = Cache()
        ctx = Context(cache)
        assert ctx.cache is cache

    def test_registers_default_providers(self):
        """Test Context registers default providers on init."""
        cache = Cache()
        ctx = Context(cache)
        assert "current_time" in ctx._providers


class TestContextBuild:
    """Test suite for Context.build method."""

    def test_includes_current_time(self):
        """Test build includes current time."""
        cache = Cache()
        ctx = Context(cache)

        result = ctx.build()

        assert "CURRENT TIME:" in result
        # Should have a reasonable date format
        assert datetime.now().strftime("%B") in result  # Month name

    def test_includes_cached_weather(self):
        """Test build includes cached weather data."""
        cache = Cache()
        cache.set("weather", {"result": '{"temp": 72}'})
        ctx = Context(cache)

        result = ctx.build()

        assert "WEATHER:" in result

    def test_includes_cached_events(self):
        """Test build includes cached events data."""
        cache = Cache()
        cache.set("events", {"result": '[{"title": "Meeting"}]'})
        ctx = Context(cache)

        result = ctx.build()

        assert "EVENTS:" in result

    def test_includes_cached_todos(self):
        """Test build includes cached todos data."""
        cache = Cache()
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

    def test_register_provider(self):
        """Test registering a custom provider."""
        cache = Cache()
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

    def test_get_returns_none_when_not_set(self):
        """Test get returns None for missing data."""
        cache = Cache()
        ctx = Context(cache)

        assert ctx.get("nonexistent") is None


class TestContextBuildSystemPrompt:
    """Test suite for Context.build_system_prompt method."""

    def test_includes_identity(self):
        """Test build_system_prompt includes Nova's identity."""
        cache = Cache()
        ctx = Context(cache)

        result = ctx.build_system_prompt()

        assert "Nova" in result
        assert "IDENTITY" in result

    def test_includes_capabilities(self):
        """Test build_system_prompt includes capabilities."""
        cache = Cache()
        ctx = Context(cache)

        result = ctx.build_system_prompt()

        assert "CAPABILITIES" in result

    def test_includes_data_context_by_default(self):
        """Test build_system_prompt includes data context by default."""
        cache = Cache()
        ctx = Context(cache)

        result = ctx.build_system_prompt()

        assert "CONTEXT:" in result
        assert "CURRENT TIME:" in result

    def test_excludes_data_context_when_disabled(self):
        """Test build_system_prompt can exclude data context."""
        cache = Cache()
        ctx = Context(cache)

        result = ctx.build_system_prompt(include_data_context=False)

        assert "CONTEXT:" not in result
        assert "CURRENT TIME:" not in result
