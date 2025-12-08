"""Intent detection module for hybrid regex + LLM classification.

This module provides intelligent intent detection using a two-step approach:
1. Fast regex matching for clear, high-confidence cases
2. LLM classification fallback for ambiguous queries

Improvements include:
- Few-shot examples for better LLM accuracy
- Usage logging for pattern analysis
- Query similarity caching to reduce LLM calls
"""

from __future__ import annotations

import json
import logging
import re
from difflib import SequenceMatcher
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from brain import Brain


class Intent(Enum):
    """Supported user intents."""

    WEATHER = "weather"
    EVENTS = "events"
    TODOS = "todos"
    REFRESH = "refresh"
    GENERAL = "general"


# Regex patterns for fast intent matching
INTENT_PATTERNS: dict[Intent, re.Pattern] = {
    Intent.WEATHER: re.compile(
        r"\b(weather|temperature|rain|forecast|cold|hot|sunny|cloudy|umbrella|degrees|jacket)\b",
        re.IGNORECASE,
    ),
    Intent.EVENTS: re.compile(
        r"\b(calendar|meeting|event|schedule|appointment|busy|free|available)\b",
        re.IGNORECASE,
    ),
    Intent.TODOS: re.compile(
        r"\b(todo|task|reminder|to-do|tasks|checklist)\b",
        re.IGNORECASE,
    ),
    Intent.REFRESH: re.compile(
        r"\b(refresh|update|latest|check again|refetch|reload)\b",
        re.IGNORECASE,
    ),
}

# Configuration
CONFIDENCE_THRESHOLD = 0.3  # Minimum probability to include intent
REGEX_HIGH_CONFIDENCE = 0.8  # Skip LLM if regex confidence >= this
CACHE_SIMILARITY_THRESHOLD = 0.85  # Similarity ratio for cache hits

# Few-shot examples for LLM classification
FEW_SHOT_EXAMPLES = """EXAMPLES:
User: "What's the weather like?"
→ {"weather": 0.95, "events": 0.0, "todos": 0.0, "refresh": 0.0}

User: "Do I have any meetings tomorrow?"
→ {"weather": 0.0, "events": 0.95, "todos": 0.0, "refresh": 0.0}

User: "Do I need an umbrella for my meeting?"
→ {"weather": 0.8, "events": 0.6, "todos": 0.0, "refresh": 0.0}

User: "What tasks do I need to finish today?"
→ {"weather": 0.0, "events": 0.25, "todos": 0.95, "refresh": 0.0}

User: "Get me the latest weather"
→ {"weather": 0.9, "events": 0.0, "todos": 0.0, "refresh": 0.7}

User: "Am I free at 3pm?"
→ {"weather": 0.0, "events": 0.9, "todos": 0.0, "refresh": 0.0}

User: "Should I bring a jacket to my appointment?"
→ {"weather": 0.85, "events": 0.7, "todos": 0.0, "refresh": 0.0}

User: "Refresh my calendar"
→ {"weather": 0.0, "events": 0.5, "todos": 0.0, "refresh": 0.95}
"""


class IntentCache:
    """Cache for LLM intent classifications.

    Uses query similarity matching to avoid redundant LLM calls
    for similar queries.
    """

    def __init__(self, similarity_threshold: float = CACHE_SIMILARITY_THRESHOLD):
        """Initialize the cache.

        Args:
            similarity_threshold: Minimum similarity ratio for cache hits.
        """
        self._cache: dict[str, dict[Intent, float]] = {}
        self._similarity_threshold = similarity_threshold
        self.logger = logging.getLogger(__name__)

    def _normalize(self, query: str) -> str:
        """Normalize query for comparison."""
        return query.lower().strip()

    def _similarity(self, a: str, b: str) -> float:
        """Calculate similarity ratio between two strings."""
        return SequenceMatcher(None, a, b).ratio()

    def get(self, query: str) -> dict[Intent, float] | None:
        """Get cached classification for a similar query.

        Args:
            query: The user's query.

        Returns:
            Cached classification if similar query found, else None.
        """
        normalized = self._normalize(query)

        # Exact match
        if normalized in self._cache:
            self.logger.debug(f"Cache hit (exact): '{query[:30]}...'")
            return self._cache[normalized]

        # Fuzzy match
        for cached_query, result in self._cache.items():
            if self._similarity(normalized, cached_query) >= self._similarity_threshold:
                self.logger.debug(f"Cache hit (similar): '{query[:30]}...'")
                return result

        return None

    def store(self, query: str, result: dict[Intent, float]) -> None:
        """Store classification result in cache.

        Args:
            query: The user's query.
            result: The classification result.
        """
        normalized = self._normalize(query)
        self._cache[normalized] = result
        self.logger.debug(f"Cached classification: '{query[:30]}...'")

    def clear(self) -> int:
        """Clear all cached entries.

        Returns:
            Number of entries cleared.
        """
        count = len(self._cache)
        self._cache.clear()
        return count


class IntentDetector:
    """Hybrid intent detector using regex + LLM classification.

    Uses fast regex matching for clear cases, falls back to LLM
    classification for ambiguous or complex queries.

    Features:
    - Few-shot examples for accurate LLM classification
    - Query similarity caching to reduce LLM calls
    - Usage logging for pattern analysis

    Attributes:
        brain: The Brain instance for LLM classification.
        cache: Intent classification cache.
        logger: Module logger instance.
    """

    def __init__(self, brain: Brain) -> None:
        """Initialize the intent detector.

        Args:
            brain: The Brain instance for LLM calls.
        """
        self.brain = brain
        self.cache = IntentCache()
        self.logger = logging.getLogger(__name__)

    def detect(self, message: str) -> set[Intent]:
        """Detect intents from a user message.

        Uses hybrid approach:
        1. Try regex matching first (fast path)
        2. If ambiguous/unclear, check cache for similar queries
        3. If cache miss, use LLM classification

        Args:
            message: The user's message.

        Returns:
            Set of detected Intent values.
        """
        # Step 1: Regex fast path
        regex_results = self._regex_match(message)
        self.logger.debug(f"Regex results: {regex_results}")

        # Check if we can skip LLM
        if not self._should_use_llm(regex_results, message):
            intents = {
                intent for intent, conf in regex_results.items() if conf >= CONFIDENCE_THRESHOLD
            }
            self.logger.info(
                f"Intent detection [regex]: '{message[:50]}' → {[i.value for i in intents]}"
            )
            return intents if intents else {Intent.GENERAL}

        # Step 2: Check cache for similar queries
        cached_results = self.cache.get(message)
        if cached_results is not None:
            # Combine with regex results
            combined = self._combine_results(regex_results, cached_results)
            intents = {intent for intent, conf in combined.items() if conf >= CONFIDENCE_THRESHOLD}
            self.logger.info(
                f"Intent detection [cache]: '{message[:50]}' → {[i.value for i in intents]}"
            )
            return intents if intents else {Intent.GENERAL}

        # Step 3: LLM classification
        self.logger.info("Using LLM for intent classification")
        llm_results = self._llm_classify(message)
        self.logger.debug(f"LLM results: {llm_results}")

        # Store in cache for future similar queries
        if llm_results:
            self.cache.store(message, llm_results)

        # Combine regex and LLM results
        combined = self._combine_results(regex_results, llm_results)

        # Filter by threshold
        intents = {intent for intent, conf in combined.items() if conf >= CONFIDENCE_THRESHOLD}

        # Log for pattern analysis
        self.logger.info(
            f"Intent detection [llm]: '{message[:50]}' → {[i.value for i in intents]} "
            f"(raw: {{{', '.join(f'{k.value}: {v:.2f}' for k, v in combined.items() if v > 0)}}})"
        )

        return intents if intents else {Intent.GENERAL}

    def _combine_results(
        self, regex_results: dict[Intent, float], other_results: dict[Intent, float]
    ) -> dict[Intent, float]:
        """Combine results from multiple sources, taking max confidence.

        Args:
            regex_results: Results from regex matching.
            other_results: Results from cache or LLM.

        Returns:
            Combined results with max confidence per intent.
        """
        combined = {}
        for intent in Intent:
            if intent == Intent.GENERAL:
                continue
            regex_conf = regex_results.get(intent, 0.0)
            other_conf = other_results.get(intent, 0.0)
            combined[intent] = max(regex_conf, other_conf)
        return combined

    def _regex_match(self, message: str) -> dict[Intent, float]:
        """Match message against regex patterns.

        Args:
            message: The user's message.

        Returns:
            Dict mapping Intent to confidence (0.0-1.0).
        """
        results = {}

        for intent, pattern in INTENT_PATTERNS.items():
            matches = pattern.findall(message)
            if matches:
                # More matches = higher confidence
                # 1 match = 0.7, 2+ matches = 0.9
                confidence = 0.7 if len(matches) == 1 else 0.9
                results[intent] = confidence

        return results

    def _should_use_llm(self, regex_results: dict[Intent, float], message: str) -> bool:
        """Decide if LLM classification is needed.

        Args:
            regex_results: Results from regex matching.
            message: The original message.

        Returns:
            True if LLM should be used.
        """
        # No regex matches - definitely use LLM
        if not regex_results:
            return True

        # Check if any match is high confidence
        high_confidence = any(conf >= REGEX_HIGH_CONFIDENCE for conf in regex_results.values())
        if high_confidence:
            return False

        # Multiple weak matches - use LLM to disambiguate
        if len(regex_results) > 1:
            return True

        # Question without clear strong match - might benefit from LLM
        return bool("?" in message and not high_confidence)

    def _llm_classify(self, message: str) -> dict[Intent, float]:
        """Use LLM to classify intent with probability distribution.

        Uses few-shot examples for improved accuracy.

        Args:
            message: The user's message.

        Returns:
            Dict mapping Intent to probability (0.0-1.0).
        """
        prompt = f"""Classify the user's intent. Return a JSON object with probabilities (0.0-1.0) for each intent.

Intents:
- weather: Questions about weather, temperature, rain, if they need umbrella/jacket
- events: Questions about calendar, meetings, schedule, availability
- todos: Questions about tasks, to-do items, reminders
- refresh: Requests to update/refresh data

{FEW_SHOT_EXAMPLES}
NOW CLASSIFY:
User: "{message}"
→ """

        try:
            response = self.brain.ai.generate_content(prompt)
            response_text = response.text.strip()

            # Extract JSON from response (handle potential markdown formatting)
            if "```" in response_text:
                json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)

            probabilities = json.loads(response_text)

            # Convert to Intent enum keys
            results = {}
            for intent in Intent:
                if intent == Intent.GENERAL:
                    continue
                prob = probabilities.get(intent.value, 0.0)
                if isinstance(prob, (int, float)) and 0 <= prob <= 1:
                    results[intent] = float(prob)

            return results

        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            self.logger.warning(f"LLM classification failed: {e}")
            return {}


def detect_intents_simple(message: str) -> set[str]:
    """Simple regex-only intent detection (backward compatible).

    This is a simplified version for use without Brain/LLM.
    Returns string intent names instead of Intent enum.

    Args:
        message: The user's message.

    Returns:
        Set of intent name strings.
    """
    intents = set()

    for intent, pattern in INTENT_PATTERNS.items():
        if pattern.search(message):
            intents.add(intent.value)

    return intents if intents else {"general"}
