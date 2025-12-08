"""Tests for the Intent module."""

from unittest.mock import MagicMock

import pytest

from intent import (
    Intent,
    IntentDetector,
    detect_intents_simple,
)


class TestIntent:
    """Test suite for Intent enum."""

    def test_intent_values(self):
        """Test Intent enum has expected values."""
        assert Intent.WEATHER.value == "weather"
        assert Intent.EVENTS.value == "events"
        assert Intent.TODOS.value == "todos"
        assert Intent.REFRESH.value == "refresh"
        assert Intent.GENERAL.value == "general"


class TestDetectIntentsSimple:
    """Test suite for simple regex-only detection."""

    def test_detects_weather(self):
        """Test detects weather intent."""
        assert "weather" in detect_intents_simple("What's the weather?")
        assert "weather" in detect_intents_simple("rain forecast today")
        assert "weather" in detect_intents_simple("temperature check")

    def test_detects_events(self):
        """Test detects events intent."""
        assert "events" in detect_intents_simple("meeting at 3pm")
        assert "events" in detect_intents_simple("Check my calendar")
        assert "events" in detect_intents_simple("appointment tomorrow")

    def test_detects_todos(self):
        """Test detects todos intent."""
        assert "todos" in detect_intents_simple("What's on my todo list?")
        assert "todos" in detect_intents_simple("Show my tasks")
        assert "todos" in detect_intents_simple("checklist for today")

    def test_detects_refresh(self):
        """Test detects refresh intent."""
        assert "refresh" in detect_intents_simple("Refresh the weather")
        assert "refresh" in detect_intents_simple("Update my data")

    def test_returns_general_for_unknown(self):
        """Test returns general for unmatched messages."""
        assert detect_intents_simple("Hello Nova") == {"general"}
        assert detect_intents_simple("Thanks!") == {"general"}

    def test_detects_multiple_intents(self):
        """Test detects multiple intents."""
        result = detect_intents_simple("weather and meeting today")
        assert "weather" in result
        assert "events" in result


class TestIntentDetectorRegex:
    """Test suite for IntentDetector regex matching."""

    @pytest.fixture
    def detector(self):
        """Create detector with mocked brain."""
        mock_brain = MagicMock()
        return IntentDetector(mock_brain)

    def test_regex_match_weather(self, detector):
        """Test regex matches weather keywords."""
        results = detector._regex_match("What's the weather?")
        assert Intent.WEATHER in results
        assert results[Intent.WEATHER] >= 0.7

    def test_regex_match_multiple_keywords_higher_confidence(self, detector):
        """Test higher confidence with multiple keywords."""
        # "weather forecast" contains two weather keywords
        results = detector._regex_match("weather forecast today")
        assert Intent.WEATHER in results
        assert results[Intent.WEATHER] == 0.9  # 2+ matches = 0.9

    def test_regex_match_no_match(self, detector):
        """Test no matches for unrelated message."""
        results = detector._regex_match("Hello there")
        assert len(results) == 0


class TestIntentDetectorShouldUseLLM:
    """Test suite for LLM fallback decision logic."""

    @pytest.fixture
    def detector(self):
        """Create detector with mocked brain."""
        mock_brain = MagicMock()
        return IntentDetector(mock_brain)

    def test_uses_llm_when_no_matches(self, detector):
        """Test uses LLM when no regex matches."""
        assert detector._should_use_llm({}, "Hello") is True

    def test_skips_llm_for_high_confidence(self, detector):
        """Test skips LLM for high confidence match."""
        regex_results = {Intent.WEATHER: 0.9}
        assert detector._should_use_llm(regex_results, "weather") is False

    def test_uses_llm_for_multiple_weak_matches(self, detector):
        """Test uses LLM for multiple weak matches."""
        regex_results = {Intent.WEATHER: 0.6, Intent.EVENTS: 0.6}
        assert detector._should_use_llm(regex_results, "weather meeting") is True

    def test_uses_llm_for_question_without_high_confidence(self, detector):
        """Test uses LLM for questions without strong match."""
        regex_results = {Intent.WEATHER: 0.7}
        assert detector._should_use_llm(regex_results, "Is it cold?") is True


class TestIntentDetectorDetect:
    """Test suite for IntentDetector.detect method."""

    @pytest.fixture
    def detector(self):
        """Create detector with mocked brain."""
        mock_brain = MagicMock()
        return IntentDetector(mock_brain)

    def test_fast_path_weather(self, detector):
        """Test fast path for clear weather query."""
        # "weather forecast" has 2 matches, so high confidence
        result = detector.detect("What's the weather forecast?")
        assert Intent.WEATHER in result

    def test_returns_general_for_greetings(self, detector):
        """Test returns GENERAL for greetings."""
        # Mock LLM to return empty (no strong intent)
        detector.brain.ai.generate_content.return_value.text = (
            '{"weather": 0.1, "events": 0.1, "todos": 0.0, "refresh": 0.0}'
        )
        result = detector.detect("Hello Nova!")
        assert Intent.GENERAL in result


class TestIntentDetectorLLMClassify:
    """Test suite for IntentDetector LLM classification."""

    def test_parses_llm_response(self):
        """Test parses LLM JSON response."""
        mock_brain = MagicMock()
        mock_brain.ai.generate_content.return_value.text = (
            '{"weather": 0.8, "events": 0.2, "todos": 0.0, "refresh": 0.0}'
        )
        detector = IntentDetector(mock_brain)

        result = detector._llm_classify("Do I need an umbrella?")

        assert Intent.WEATHER in result
        assert result[Intent.WEATHER] == 0.8

    def test_handles_markdown_code_block(self):
        """Test extracts JSON from markdown code block."""
        mock_brain = MagicMock()
        mock_brain.ai.generate_content.return_value.text = """```json
{"weather": 0.9, "events": 0.0, "todos": 0.0, "refresh": 0.0}
```"""
        detector = IntentDetector(mock_brain)

        result = detector._llm_classify("Is it raining?")

        assert Intent.WEATHER in result
        assert result[Intent.WEATHER] == 0.9

    def test_handles_invalid_json(self):
        """Test returns empty dict on invalid JSON."""
        mock_brain = MagicMock()
        mock_brain.ai.generate_content.return_value.text = "not valid json"
        detector = IntentDetector(mock_brain)

        result = detector._llm_classify("test")

        assert result == {}
