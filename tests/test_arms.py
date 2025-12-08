"""Tests for the Arms (HTTP client) module."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from arms import Arms


class TestArms:
    """Test suite for Arms HTTP client."""

    def test_initialization(self):
        """Test Arms initializes with None client."""
        arms = Arms()
        assert arms.client is None

    def test_start_creates_client(self):
        """Test that start() creates an AsyncClient."""
        arms = Arms()
        arms.start()

        assert arms.client is not None
        assert isinstance(arms.client, httpx.AsyncClient)

    @pytest.mark.asyncio
    async def test_stop_closes_client(self):
        """Test that stop() properly closes the client."""
        arms = Arms()
        arms.start()

        await arms.stop()

        assert arms.client is None

    @pytest.mark.asyncio
    async def test_stop_handles_none_client(self):
        """Test that stop() handles case where client is None."""
        arms = Arms()
        # Should not raise
        await arms.stop()

    def test_call_returns_client(self):
        """Test __call__ returns the client."""
        arms = Arms()
        arms.start()

        client = arms()
        assert client is arms.client

    def test_call_raises_when_not_started(self):
        """Test __call__ raises AssertionError when client not started."""
        arms = Arms()

        with pytest.raises(AssertionError):
            arms()

    @pytest.mark.asyncio
    async def test_get_success(self):
        """Test successful GET request."""
        arms = Arms()
        arms.start()

        mock_response = MagicMock()
        mock_response.text = '{"data": "test"}'
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with patch.object(arms.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await arms.get("https://example.com")

            assert result["status"] == 200
            assert result["result"] == '{"data": "test"}'

        await arms.stop()

    @pytest.mark.asyncio
    async def test_get_http_error(self):
        """Test GET request with HTTP error."""
        arms = Arms()
        arms.start()

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                "Not found", request=MagicMock(), response=mock_response
            )
        )

        with patch.object(arms.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await arms.get("https://example.com/notfound")

            assert result["status"] == 404
            assert result["result"] is None

        await arms.stop()

    @pytest.mark.asyncio
    async def test_get_weather_builds_correct_url(self):
        """Test get_weather uses WeatherAPI to build URL."""
        arms = Arms()
        arms.start()

        with patch.object(arms, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"result": "{}", "status": 200}

            await arms.get_weather()

            # Verify get was called with a weather API URL
            call_args = mock_get.call_args[0][0]
            assert "api.open-meteo.com" in call_args

        await arms.stop()

    @pytest.mark.asyncio
    async def test_get_events_success(self):
        """Test get_events returns formatted calendar events from all calendars."""
        from apis.calendar import CalendarAPI

        arms = Arms()
        arms.start()

        mock_events = [
            {"id": "1", "summary": "Meeting", "start": "10:00", "end": "11:00", "calendar": "Work"},
        ]

        with patch.object(CalendarAPI, "get_all_events", return_value=mock_events):
            result = await arms.get_events("2025-01-15")

            assert result["status"] == 200
            assert '"Meeting"' in result["result"]
            assert '"Work"' in result["result"]

        await arms.stop()

    @pytest.mark.asyncio
    async def test_get_events_handles_error(self):
        """Test get_events handles CalendarAPIError gracefully."""
        from apis.calendar import CalendarAPI, CalendarAPIError

        arms = Arms()
        arms.start()

        with patch.object(
            CalendarAPI, "get_all_events", side_effect=CalendarAPIError("Test error")
        ):
            result = await arms.get_events("2025-01-15")

            assert result["status"] == 500
            assert result["result"] is None

        await arms.stop()
