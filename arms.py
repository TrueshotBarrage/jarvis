import logging

from time import time
from typing import Optional

import httpx
import asyncio

from apis.weather import WeatherAPI


class Arms:
    def __init__(self):
        # Set up logging
        self.logger = logging.getLogger(__name__)

        self.client = None

        self.logger.info(
            "Useful appendages fully functional and ready to grab things at your command!"
        )

    def __call__(self):
        """Calling the instantiated Arms returns the wrapped singleton."""
        # Ensure we don't use it if not started / running
        assert self.client is not None
        self.logger.info(
            f"httpx client.is_closed(): {self.client.is_closed}. ID (will be unchanged): {id(self.client)}"
        )
        return self.client

    def start(self):
        """Instantiate the client. Call from the FastAPI startup hook."""
        self.client = httpx.AsyncClient()
        self.logger.info(f"httpx AsyncClient started. ID {id(self.client)}")

    async def stop(self):
        """Gracefully shut down. Call from the FastAPI shutdown hook."""
        self.logger.info(
            f"httpx client.is_closed(): {self.client.is_closed} - Now can be closed. ID (will be unchanged): {id(self.client)}"
        )
        await self.client.aclose()
        self.logger.info(
            f"httpx client.is_closed(): {self.client.is_closed}. ID (will be unchanged): {id(self.client)}"
        )
        self.client = None
        self.logger.info("httpx AsyncClient closed.")

    async def get(self, url, params=None) -> dict:
        res = None
        try:
            res = await self.client.get(url, params=params)
            res.raise_for_status()

        except httpx.HTTPError as e:
            self.logger.error(f"Error: {e}")
            return {"result": None, "status": res.status_code if res else 404}

        return {"result": res.text, "status": res.status_code}

    async def get_weather(self):
        weather_api = WeatherAPI()
        weather_url = weather_api.build_url()
        weather = await self.get(weather_url)

        return weather

    async def get_todos(self, day):
        todoist_url = f"/route/to/todoist/api/{day}"

        # TODO: Set up Todoist API, including params={API key, ...}
        todos = await self.get(todoist_url)

        return todos

    async def get_events(self, day):
        gcal_url = f"/route/to/gcal/api/{day}"

        # TODO: Set up Google Calendar API, including params={API key, scopes, ...}
        events = await self.get(gcal_url)

        return events

    async def run_autobudget_pipeline(self):
        # TODO: Set up a server instance (cloud or RPi and establish a fixed endpoint)
        endpoint_base = ""
        endpoint_run = f"{endpoint_base}/run"
        result = await self.get(endpoint_run)

        return result
