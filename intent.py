"""Intent detection module for hybrid regex + LLM classification.

This module provides intelligent intent detection using a two-step approach:
1. Fast regex matching for clear, high-confidence cases
2. LLM classification fallback for ambiguous queries
"""

from __future__ import annotations

import json
import logging
import re
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
# Moved from heart.py and enhanced
INTENT_PATTERNS: dict[Intent, re.Pattern] = {
    Intent.WEATHER: re.compile(
        r"\b(weather|temperature|rain|forecast|cold|hot|sunny|cloudy|umbrella|degrees)\b",
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


class IntentDetector:
    """Hybrid intent detector using regex + LLM classification.

    Uses fast regex matching for clear cases, falls back to LLM
    classification for ambiguous or complex queries.

    Attributes:
        brain: The Brain instance for LLM classification.
        logger: Module logger instance.
    """

    def __init__(self, brain: Brain) -> None:
        """Initialize the intent detector.

        Args:
            brain: The Brain instance for LLM calls.
        """
        self.brain = brain
        self.logger = logging.getLogger(__name__)

    def detect(self, message: str) -> set[Intent]:
        """Detect intents from a user message.

        Uses hybrid approach:
        1. Try regex matching first (fast path)
        2. If ambiguous/unclear, use LLM classification

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
            self.logger.info(f"Fast path intents: {intents}")
            return intents if intents else {Intent.GENERAL}

        # Step 2: LLM classification
        self.logger.info("Using LLM for intent classification")
        llm_results = self._llm_classify(message)
        self.logger.debug(f"LLM results: {llm_results}")

        # Combine regex and LLM results, taking max confidence
        combined = {}
        for intent in Intent:
            if intent == Intent.GENERAL:
                continue
            regex_conf = regex_results.get(intent, 0.0)
            llm_conf = llm_results.get(intent, 0.0)
            combined[intent] = max(regex_conf, llm_conf)

        # Filter by threshold
        intents = {intent for intent, conf in combined.items() if conf >= CONFIDENCE_THRESHOLD}

        self.logger.info(f"Final intents: {intents}")
        return intents if intents else {Intent.GENERAL}

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

        Note: This is a first iteration. Future improvements could include:
        - Few-shot examples for better accuracy
        - Fine-tuned prompt based on error analysis
        - Caching of similar queries

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

User message: "{message}"

Respond with ONLY a JSON object, no other text. Example:
{{"weather": 0.8, "events": 0.2, "todos": 0.0, "refresh": 0.0}}

JSON:"""

        try:
            response = self.brain.ai.generate_content(prompt)
            response_text = response.text.strip()

            # Extract JSON from response (handle potential markdown formatting)
            if "```" in response_text:
                # Extract from code block
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
