"""Tests for the Weather API wrapper."""

from unittest.mock import patch

from apis.weather import WeatherAPI


class TestWeatherAPI:
    """Test suite for WeatherAPI class."""

    @patch("apis.weather.settings")
    def test_default_initialization(self, mock_settings):
        """Test that WeatherAPI initializes with default values."""
        mock_settings.weather_lat = 40.789
        mock_settings.weather_lon = -73.967

        api = WeatherAPI()

        assert api.base_url == "https://api.open-meteo.com/v1/forecast"
        assert api.params["latitude"] == 40.789
        assert api.params["longitude"] == -73.967
        assert api.params["temperature_unit"] == "fahrenheit"
        assert api.params["timezone"] == "America/New_York"

    def test_set_coordinates(self):
        """Test setting custom coordinates."""
        api = WeatherAPI()
        result = api.set_coordinates(lat=34.0522, lon=-118.2437)

        # Should return self for chaining
        assert result is api
        assert api.params["latitude"] == 34.0522
        assert api.params["longitude"] == -118.2437

    def test_set_temperature_unit(self):
        """Test setting temperature unit."""
        api = WeatherAPI()
        api.set_temperature_unit("celsius")

        assert api.params["temperature_unit"] == "celsius"

    def test_set_timezone(self):
        """Test setting timezone."""
        api = WeatherAPI()
        api.set_timezone("America/Los_Angeles")

        assert api.params["timezone"] == "America/Los_Angeles"

    def test_set_current_params(self):
        """Test setting current weather parameters."""
        api = WeatherAPI()
        api.set_current("temperature_2m")

        assert api.params["current"] == ["temperature_2m"]

    def test_set_daily_params(self):
        """Test setting daily weather parameters."""
        api = WeatherAPI()
        api.set_daily("temperature_2m_max", "sunrise")

        assert api.params["daily"] == ["temperature_2m_max", "sunrise"]

    def test_build_url(self):
        """Test URL building with parameters."""
        api = WeatherAPI()
        api.set_coordinates(40.0, -74.0)
        api.set_current("temperature_2m")
        api.set_daily("sunrise", "sunset")

        url = api.build_url()

        assert "https://api.open-meteo.com/v1/forecast?" in url
        assert "latitude=40.0" in url
        assert "longitude=-74.0" in url
        assert "current=temperature_2m" in url
        assert "daily=sunrise,sunset" in url

    def test_with_current_translation(self):
        """Test fluent API with parameter translation."""
        api = WeatherAPI()
        api.with_current("temp", "rain")

        assert api.params["current"] == ["temperature_2m", "precipitation"]

    def test_with_daily_translation(self):
        """Test fluent API with daily parameter translation."""
        api = WeatherAPI()
        api.with_daily("max_temp", "rain_hours")

        assert api.params["daily"] == ["temperature_2m_max", "precipitation_hours"]

    def test_method_chaining(self):
        """Test that setter methods can be chained."""
        api = WeatherAPI()
        result = (
            api.set_coordinates(40.0, -74.0)
            .set_temperature_unit("celsius")
            .set_timezone("America/Chicago")
            .with_current("temp")
            .with_daily("max_temp")
        )

        assert result is api
        assert api.params["latitude"] == 40.0
        assert api.params["temperature_unit"] == "celsius"
        assert api.params["timezone"] == "America/Chicago"
