"""Heart module - Central coordinator and FastAPI server for Jarvis.

This is the main entry point that orchestrates all Jarvis components:
Brain (AI), Arms (HTTP client), and Mouth (TTS).
"""

import datetime
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from arms import Arms
from brain import Brain
from mouth import Mouth


def become_intelligent():
    return Brain()


def attach_arms():
    return Arms()


def unmute() -> Mouth:
    """Initialize the text-to-speech module."""
    return Mouth()


logging.basicConfig(
    level=logging.INFO, format="%(levelname)-9s %(asctime)s - [%(name)s] %(message)s"
)
vitals = logging.getLogger("Jarvis")

vitals.info("Coming to life...")
brain = become_intelligent()
arms = attach_arms()
mouth = unmute()
vitals.info("All systems functional. Jarvis is ready! How is your day, sir?")

jarvis_actions = {
    "weather": "/weather",
    "todos": "/todos",
    "calendar": "/events",
    "daily_routine": "/daily",
    "introduction": "/intro",
}


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    # On startup
    arms.start()
    # Run the application
    yield
    # On shutdown
    await arms.stop()


app = FastAPI(lifespan=lifespan)


@app.get("/test")
async def test_external_api():
    """Test external API connectivity."""
    res = await arms.get("https://stackoverflow.com")
    vitals.info(f"External API response: {res['status']}")
    return res


# @app.post("/user_input")
# async def process_user_input(user_input: str):
#     res = brain.choose(user_input, list(jarvis_actions.keys()), get_probabilities=True)
#     # The expected response is a dict of actions to probabilities, so let's call the correct action
#     res[]
#     return {"result": response, "status": 200}


@app.get("/weather")
async def get_weather():
    """Get current weather forecast from Open-Meteo API."""
    # Invoke the weather API
    weather_res = await arms.get_weather()

    # Check if the API call was successful
    api_status_code = weather_res["status"]
    if api_status_code != 200:
        vitals.error(f"Error fetching weather: {api_status_code}")
        return None

    # Parse the weather data
    weather = weather_res["result"] = json.loads(weather_res["result"])

    # Output the weather
    vitals.info(f"Today's weather: {weather}")

    # Return a response
    return weather


@app.get("/daily")
async def run_daily_routine():
    """Run daily routine: fetch weather and calendar events, speak summary aloud."""
    # Get today's date
    today = datetime.date.today().isoformat()

    # Collect speech outputs to consolidate into a single audio file
    speech_parts: list[str] = []

    # Invoke the weather API
    weather_res = await arms.get_weather()

    # Check if the API call was successful
    api_status_code = weather_res["status"]
    if api_status_code != 200:
        vitals.error(f"Error fetching weather: {api_status_code}")
        weather = None
    else:
        weather = json.loads(weather_res["result"])
        vitals.info(f"Today's weather: {weather}")

    # Fetch calendar events
    events_res = await arms.get_events(today)
    if events_res["status"] == 200 and events_res["result"]:
        events = json.loads(events_res["result"])
        vitals.info(f"Today's events: {len(events)} events found")
    else:
        events = []
        vitals.warning("Could not fetch calendar events")

    # todos_today = await arms.get_todos(today)

    # Generate weather summary
    if weather:
        weather_prompt_context = (
            "Given the weather API response data, generate a concise and engaging "
            "message suitable for a personal assistant to read aloud. The message should "
            "include current temperature, chance of rain, and any notable weather events "
            "for today. Include a brief description of the highs and lows of the daily "
            "weather, if it exists, as well as sunrise and sunset times. "
            "Ensure the message is friendly and easy to understand. "
            "IMPORTANT: Output plain text only - no markdown, no asterisks, no bullet "
            "points, no formatting. This will be read aloud by text-to-speech."
        )
        weather_output = brain.process(
            weather, request_type="api_data", context=weather_prompt_context
        )
        speech_parts.append(weather_output)

    # Generate calendar summary
    if events:
        events_prompt_context = (
            "Given the calendar events data, generate a concise and engaging "
            "message suitable for a personal assistant to read aloud. Summarize "
            "the events for today including their times and titles. Group events "
            "by calendar if multiple calendars are present. If there are many events, "
            "prioritize the most important ones. Keep it brief and easy to understand. "
            "IMPORTANT: Output plain text only - no markdown, no asterisks, no bullet "
            "points, no formatting. This will be read aloud by text-to-speech."
        )
        events_output = brain.process(
            events, request_type="api_data", context=events_prompt_context
        )
        speech_parts.append(events_output)

    # Generate consolidated audio file from all speech parts
    if speech_parts:
        combined_speech = " ".join(speech_parts)
        mouth.speak(combined_speech)

    # Return full response
    return {"weather": weather, "events": events, "status": 200}


@app.get("/events")
async def get_events():
    """Get today's calendar events from Google Calendar."""
    today = datetime.date.today().isoformat()

    events_res = await arms.get_events(today)

    # Check if the API call was successful
    api_status_code = events_res["status"]
    if api_status_code != 200:
        vitals.error(f"Error fetching events: {api_status_code}")
        return None

    # Parse and return the events
    events = json.loads(events_res["result"]) if events_res["result"] else []
    vitals.info(f"Today's events: {events}")

    return events


@app.get("/intro")
async def get_introduction():
    """Get AI-generated assistant introduction."""
    # Include today's date in the introduction
    today = datetime.date.today()

    prompt = (
        "Your name is Nova, a personal virtual assistant. "
        "Give me a brief introduction to yourself in less than 30 words."
        "Feel free to incorporate the following information (today):"
    )
    vocal_output = brain.process(today, request_type="api_data", context=prompt)
    mouth.speak(vocal_output)

    # Return a response
    return {"result": "Test API response", "status": 200}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(f"{__name__}:app", host="127.0.0.1", port=8000)
