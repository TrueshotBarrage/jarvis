"""Tests for the Brain (AI) module."""

from unittest.mock import MagicMock, patch


class TestBrain:
    """Test suite for Brain AI module."""

    @patch("brain.genai")
    def test_initialization_success(self, mock_genai, mock_secrets):
        """Test Brain initializes successfully with valid secrets."""
        # Setup mock
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Hello!"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        from brain import Brain

        Brain(secrets_file=mock_secrets)

        # Verify Gemini was configured
        mock_genai.configure.assert_called_once_with(api_key="test-api-key")
        mock_genai.GenerativeModel.assert_called_once_with("gemma-3-27b-it")

    @patch("brain.genai")
    def test_process_api_data(self, mock_genai, mock_secrets):
        """Test process() with api_data request type."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Processed response"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        from brain import Brain

        brain = Brain(secrets_file=mock_secrets)

        result = brain.process(
            message='{"temp": 72}', request_type="api_data", context="Describe the weather"
        )

        assert result == "Processed response"

    @patch("brain.genai")
    def test_process_choose(self, mock_genai, mock_secrets):
        """Test process() with choose request type."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "weather"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        from brain import Brain

        brain = Brain(secrets_file=mock_secrets)

        result = brain.process(
            message="What's the temperature?",
            request_type="choose",
            context=["weather", "calendar", "todos"],
        )

        assert result == "weather"

    @patch("brain.genai")
    def test_process_unknown_type(self, mock_genai, mock_secrets):
        """Test process() with unknown request type returns default."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Hello!"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        from brain import Brain

        brain = Brain(secrets_file=mock_secrets)

        result = brain.process(message="test", request_type="unknown_type", context=None)

        assert result == "Hello world!"

    @patch("brain.genai")
    def test_choose_returns_string(self, mock_genai, mock_secrets):
        """Test choose() returns string when get_probabilities=False."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "weather"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        from brain import Brain

        brain = Brain(secrets_file=mock_secrets)

        result = brain.choose(
            user_input="What's the weather?",
            options=["weather", "calendar"],
            get_probabilities=False,
        )

        assert result == "weather"

    @patch("brain.genai")
    def test_choose_returns_probabilities(self, mock_genai, mock_secrets):
        """Test choose() returns dict when get_probabilities=True."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"weather": 0.8, "calendar": 0.2}'
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        from brain import Brain

        brain = Brain(secrets_file=mock_secrets)

        result = brain.choose(
            user_input="What's the weather?",
            options=["weather", "calendar"],
            get_probabilities=True,
        )

        assert isinstance(result, dict)
        assert result["weather"] == 0.8
        assert result["calendar"] == 0.2
