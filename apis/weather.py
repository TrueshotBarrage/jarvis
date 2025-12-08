class WeatherAPI:
    """
    This class is a wrapper around the Open-Meteo Weather API.
    It allows you to easily construct the URL and parameters needed to query the API.

    Args:
    - latitude (float): The latitude of the location you want the weather for.
    - longitude (float): The longitude of the location you want the weather for.
    - current (list): A list of current weather parameters to be returned. Valid values are:
        - temperature_2m
        - precipitation
    - daily (list): A list of daily weather parameters to be returned. Valid values are:
        - temperature_2m_max
        - temperature_2m_min
        - sunrise
        - sunset
        - precipitation_hours
    - temperature_unit (str): The unit of temperature to use. Valid values are:
        - celsius
        - fahrenheit
    - timezone (str): The timezone to use. Valid values are:
        - America/New_York
        - America/Los_Angeles
        - America/Chicago
        - America/Denver
    """

    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.params = {
            "latitude": 40.784208,
            "longitude": -73.980252,
            "current": ["temperature_2m", "precipitation"],
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "sunrise",
                "sunset",
                "precipitation_hours",
            ],
            "temperature_unit": "fahrenheit",
            "timezone": "America/New_York",
        }

    def set_coordinates(self, lat: float, lon: float) -> "WeatherAPI":
        """Set the coordinates of the location you want the weather for.

        Args:
            - lat (float): The latitude of the location you want the weather for.
            - lon (float): The longitude of the location you want the weather for.

        Returns:
            - self: The current instance of the class.
        """
        self.params["latitude"] = lat
        self.params["longitude"] = lon
        return self

    def set_current(self, *params):
        """Set the parameters for the current weather.

        Args:
            - *params: The parameters to include in the current weather forecast.
                Valid values are:
                    - temperature_2m
                    - precipitation

        Returns:
            - self: The current instance of the class.
        """
        self.params["current"] = list(params)
        return self

    def set_daily(self, *params):
        """Set the parameters for the daily weather.

        Args:
            - *params: The parameters to include in the daily weather forecast.
                Valid values are:
                    - temperature_2m_max
                    - temperature_2m_min
                    - sunrise
                    - sunset
                    - precipitation_hours

        Returns:
            - self: The current instance of the class.
        """
        self.params["daily"] = list(params)
        return self

    def set_temperature_unit(self, unit):
        """Set the unit of temperature to use.

        Args:
            - unit (str): The unit of temperature to use. Valid values are:
                - celsius
                - fahrenheit

        Returns:
            - self: The current instance of the class.
        """
        self.params["temperature_unit"] = unit
        return self

    def set_timezone(self, tz):
        """Set the timezone to use.

        Args:
            - tz (str): The timezone to use. Valid values are:
                - America/New_York
                - America/Los_Angeles
                - America/Chicago
                - America/Denver

        Returns:
            - self: The current instance of the class.
        """
        self.params["timezone"] = tz
        return self

    def build_url(self):
        """Build the URL with the current parameters.

        Returns:
            - str: The URL with the current parameters.
        """
        params = "&".join(
            f"{k}={','.join(v)}" if isinstance(v, list) else f"{k}={v}"
            for k, v in self.params.items()
        )

        return f"{self.base_url}?{params}"

    def with_current(self, *params):
        """Set the parameters for the current weather.

        Args:
            - *params: The parameters to include in the current weather forecast.
                Valid values are:
                    - temp
                    - rain

        Returns:
            - self: The current instance of the class.

        Example: weather_api.with_current('temp', 'rain')
        """
        return self.set_current(*[self._to_english(p) for p in params])

    def with_daily(self, *params):
        """Set the parameters for the daily weather.

        Args:
            - *params: The parameters to include in the daily weather forecast.
                Valid values are:
                    - max_temp
                    - min_temp
                    - sunrise
                    - sunset
                    - rain_hours

        Returns:
            - self: The current instance of the class.

        Example: weather_api.with_daily('max_temp', 'rain_hours')
        """
        return self.set_daily(*[self._to_english(p) for p in params])

    @staticmethod
    def _to_english(param):
        """Translate parameter names to English.

        Args:
            - param (str): The parameter name to translate.

        Returns:
            - str: The English translation of the parameter name.
        """
        translations = {
            "temp": "temperature_2m",
            "rain": "precipitation",
            "max_temp": "temperature_2m_max",
            "min_temp": "temperature_2m_min",
            "sunrise": "sunrise",
            "sunset": "sunset",
            "rain_hours": "precipitation_hours",
        }
        return translations.get(param, param)
