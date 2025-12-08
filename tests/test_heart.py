"""Integration tests for the FastAPI server (heart.py).

These tests require careful mocking because heart.py initializes
components at module level.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# We need to mock before importing heart
@pytest.fixture(scope="module")
def mock_components():
    """Mock all components before heart.py is imported."""
    with (
        patch("jarvis.brain.genai") as mock_genai,
        patch("jarvis.mouth.gTTS") as mock_gtts,
        patch("jarvis.mouth.playsound3") as mock_playsound,
        patch("jarvis.mouth.pydub") as mock_pydub,
    ):
        # Setup Brain mock
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Mocked AI response"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        # Setup Mouth mocks
        mock_tts_instance = MagicMock()
        mock_gtts.return_value = mock_tts_instance
        mock_sound = MagicMock()
        mock_pydub.AudioSegment.from_file.return_value = mock_sound
        mock_sound.speedup.return_value = mock_sound

        yield {
            "genai": mock_genai,
            "gtts": mock_gtts,
            "playsound": mock_playsound,
            "pydub": mock_pydub,
        }


class TestHeartAPIUnit:
    """Unit tests for heart.py that don't require the full app."""

    def test_jarvis_actions_defined(self, mock_components):  # noqa: ARG002
        """Test that jarvis_actions mapping is defined."""
        import jarvis.heart as heart

        assert "weather" in heart.jarvis_actions
        assert "todos" in heart.jarvis_actions
        assert "calendar" in heart.jarvis_actions
        assert "daily_routine" in heart.jarvis_actions


@pytest.fixture
def app_client(mock_components):  # noqa: ARG001
    """Create a test client for the FastAPI app."""
    from httpx import ASGITransport, AsyncClient

    import jarvis.heart as heart

    return AsyncClient(transport=ASGITransport(app=heart.app), base_url="http://test")


class TestHeartAPIIntegration:
    """Integration tests for FastAPI endpoints."""

    @pytest.mark.asyncio
    async def test_weather_endpoint_success(self, app_client, mock_components):  # noqa: ARG002
        """Test /weather endpoint returns weather data on success."""
        import jarvis.heart as heart

        with patch.object(heart.arms, "get_weather", new_callable=AsyncMock) as mock_get_weather:
            mock_get_weather.return_value = {
                "result": '{"latitude": 40.78, "current": {"temperature_2m": 65}}',
                "status": 200,
            }

            async with app_client as client:
                response = await client.get("/weather")

            assert response.status_code == 200
            data = response.json()
            assert "latitude" in data

    @pytest.mark.asyncio
    async def test_weather_endpoint_api_error(self, app_client, mock_components):  # noqa: ARG002
        """Test /weather endpoint handles API errors gracefully."""
        import jarvis.heart as heart

        with patch.object(heart.arms, "get_weather", new_callable=AsyncMock) as mock_get_weather:
            mock_get_weather.return_value = {"result": None, "status": 500}

            async with app_client as client:
                response = await client.get("/weather")

            # Should return None on error
            assert response.json() is None

    @pytest.mark.asyncio
    async def test_intro_endpoint(self, app_client, mock_components):  # noqa: ARG002
        """Test /intro endpoint returns response."""
        async with app_client as client:
            response = await client.get("/intro")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == 200

    @pytest.mark.asyncio
    async def test_events_endpoint_success(self, app_client, mock_components):  # noqa: ARG002
        """Test /events endpoint returns calendar events."""
        import jarvis.heart as heart

        with patch.object(heart.arms, "get_events", new_callable=AsyncMock) as mock_get_events:
            mock_get_events.return_value = {
                "result": '[{"id": "1", "summary": "Team Meeting"}]',
                "status": 200,
            }

            async with app_client as client:
                response = await client.get("/events")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_events_endpoint_api_error(self, app_client, mock_components):  # noqa: ARG002
        """Test /events endpoint handles API errors gracefully."""
        import jarvis.heart as heart

        with patch.object(heart.arms, "get_events", new_callable=AsyncMock) as mock_get_events:
            mock_get_events.return_value = {"result": None, "status": 500}

            async with app_client as client:
                response = await client.get("/events")

            assert response.json() is None

    @pytest.mark.asyncio
    async def test_daily_includes_events(self, app_client, mock_components):  # noqa: ARG002
        """Test /daily endpoint fetches weather, events, and todos."""
        import jarvis.heart as heart

        with (
            patch.object(heart.arms, "get_weather", new_callable=AsyncMock) as mock_weather,
            patch.object(heart.arms, "get_events", new_callable=AsyncMock) as mock_events,
            patch.object(heart.arms, "get_todos", new_callable=AsyncMock) as mock_todos,
        ):
            mock_weather.return_value = {
                "result": '{"current": {"temperature_2m": 65}}',
                "status": 200,
            }
            mock_events.return_value = {
                "result": '[{"summary": "Meeting"}]',
                "status": 200,
            }
            mock_todos.return_value = {
                "result": '[{"content": "Buy groceries"}]',
                "status": 200,
            }

            async with app_client as client:
                response = await client.get("/daily")

            assert response.status_code == 200
            data = response.json()
            assert "weather" in data
            assert "events" in data
            assert "todos" in data
            mock_events.assert_called_once()
            mock_todos.assert_called_once()

    @pytest.mark.asyncio
    async def test_todos_endpoint_success(self, app_client, mock_components):  # noqa: ARG002
        """Test /todos endpoint returns tasks."""
        import jarvis.heart as heart

        with patch.object(heart.arms, "get_todos", new_callable=AsyncMock) as mock_get_todos:
            mock_get_todos.return_value = {
                "result": '[{"id": "1", "content": "Buy groceries", "priority": 2}]',
                "status": 200,
            }

            async with app_client as client:
                response = await client.get("/todos")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert data[0]["content"] == "Buy groceries"

    @pytest.mark.asyncio
    async def test_todos_endpoint_api_error(self, app_client, mock_components):  # noqa: ARG002
        """Test /todos endpoint handles API errors gracefully."""
        import jarvis.heart as heart

        with patch.object(heart.arms, "get_todos", new_callable=AsyncMock) as mock_get_todos:
            mock_get_todos.return_value = {"result": None, "status": 500}

            async with app_client as client:
                response = await client.get("/todos")

            assert response.json() is None
