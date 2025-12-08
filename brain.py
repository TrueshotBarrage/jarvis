"""Brain module - AI integration for Jarvis using Google Gemini.

This module provides LLM-powered processing for natural language understanding,
intent classification, and content generation.
"""

import json
import logging

import google.api_core.exceptions
import google.generativeai as genai


class Brain:
    """AI processing unit using Google Gemini for intelligent operations.

    Attributes:
        logger: Module logger instance.
        ai: Gemini generative model instance.
    """

    def __init__(self, secrets_file: str = "secrets.json") -> None:
        """Initialize the Brain with Gemini AI connection.

        Args:
            secrets_file: Path to JSON file containing API keys.
        """
        self.logger = logging.getLogger(__name__)

        # Load API key from secrets file
        self.logger.info("Reading secrets from config...")
        with open(secrets_file) as f:
            secrets = json.load(f)
        gemini_api_key = secrets["gemini_api_key"]
        self.logger.info("Secrets fully initialized.")

        # Initialize Gemini AI
        self.logger.info("Establishing handshake protocol with Gemini...")
        genai.configure(api_key=gemini_api_key)
        self.ai = genai.GenerativeModel("gemma-3-27b-it")

        self._verify_connection()

    def _verify_connection(self) -> None:
        """Test the Gemini API connection with a timeout."""
        try:
            conn_test_res = self.ai.generate_content("Test!", request_options={"timeout": 10})
            conn_success = conn_test_res.text.strip()
            self.logger.info(f"Gemini: {conn_success}")
            self.logger.info("Contact established with Gemini servers.")
            self.logger.info("Intelligence cortex fully activated and ready to go!")
        except google.api_core.exceptions.DeadlineExceeded as e:
            self.logger.warning(f"Gemini timeout error: {e}")
            self.logger.warning(
                "Error establishing handshake with Gemini servers. "
                "Check your connection to the multiverse grid?"
            )
            self.logger.info(
                "Intelligence cortex activated, but cannot reach multiverse grid network. "
                "Complex thought processing may not be available."
            )

    def process(self, message: str, request_type: str, context: str | None = None) -> str:
        """Process a message using the AI model.

        Args:
            message: The input message or data to process.
            request_type: Type of processing - 'api_data', 'choose', or 'choose_distribution'.
            context: Additional context or instructions for the AI.

        Returns:
            The AI-generated response text.
        """
        if request_type == "api_data":
            prompt = f"{context}\n{message}" if context is not None else str(message)
            thought = self.ai.generate_content(prompt)
            return thought.text

        elif request_type == "choose":
            prompt = (
                f"The user is saying: '{message}'. Based on this input, choose "
                f"the most likely option that the user is suggesting from the following options: "
                f"{context}"
            )
            thought = self.ai.generate_content(prompt)
            return thought.text

        elif request_type == "choose_distribution":
            prompt = (
                f"The user is saying: '{message}'. Based on this input, provide a normalized "
                f"probability distribution of the likelihood of each option that the user is suggesting "
                f"from the following options: "
                f"{context}"
                f"\nFormat the output as a JSON object with the keys being the options and the values being the "
                f"probability of that option, with the keys sorted in descending order of probability. "
                f"For example: {{'Option 1': 0.5, 'Option 2': 0.3, 'Option 3': 0.2}}."
            )
            thought = self.ai.generate_content(prompt)
            return thought.text

        return "Hello world!"

    def choose(
        self, user_input: str, options: list[str], get_probabilities: bool = False
    ) -> str | dict[str, float]:
        """Classify user input into one of the provided options.

        Args:
            user_input: The user's message to classify.
            options: List of possible action/intent options.
            get_probabilities: If True, return probability distribution over options.

        Returns:
            Either a single option string, or a dict mapping options to probabilities.

        Raises:
            json.JSONDecodeError: If probability mode fails to parse AI response.
        """
        choose_type = "choose_distribution" if get_probabilities else "choose"
        likely_option = self.process(user_input, choose_type, str(options))

        if get_probabilities:
            likely_option = json.loads(likely_option)

        return likely_option

    def chat(
        self,
        user_message: str,
        history: list[dict[str, str]] | None = None,
        system_prompt: str = "",
    ) -> str:
        """Generate a response with conversation history.

        Uses Gemini's multi-turn conversation format for context-aware responses.

        Args:
            user_message: The current user message.
            history: Previous conversation messages as list of
                {'role': 'user'|'assistant', 'content': '...'} dicts.
            system_prompt: Complete system prompt from Context.build_system_prompt().

        Returns:
            The AI-generated response text.
        """
        # Use provided system prompt or fallback to minimal prompt
        if not system_prompt:
            system_prompt = "You are Nova, a helpful AI assistant."

        # Build multi-turn conversation format for Gemini
        contents = []

        # Add system instruction as first user message
        contents.append(
            {
                "role": "user",
                "parts": [{"text": f"[System: {system_prompt}]"}],
            }
        )
        contents.append(
            {
                "role": "model",
                "parts": [{"text": "Understood. I'm Nova, ready to help!"}],
            }
        )

        # Add conversation history
        if history:
            for msg in history:
                role = "model" if msg["role"] == "assistant" else "user"
                contents.append(
                    {
                        "role": role,
                        "parts": [{"text": msg["content"]}],
                    }
                )

        # Add current user message
        contents.append(
            {
                "role": "user",
                "parts": [{"text": user_message}],
            }
        )

        # Generate response
        self.logger.debug(f"Chat with {len(contents)} messages")
        response = self.ai.generate_content(contents)

        return response.text
