"""Heart module - Central coordinator and FastAPI server for Jarvis.

This is the main entry point that orchestrates all Jarvis components:
Brain (AI), Arms (HTTP client), Mouth (TTS), Memory, and Cache.
"""

import datetime
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from arms import Arms
from brain import Brain
from cache import Cache
from context import Context
from intent import Intent, IntentDetector
from memory import Memory
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
memory = Memory()
cache = Cache()
context_mgr = Context(cache)
intent_detector = IntentDetector(brain)
vitals.info("All systems functional. Jarvis is ready! How is your day, sir?")

jarvis_actions = {
    "weather": "/weather",
    "todos": "/todos",
    "calendar": "/events",
    "daily_routine": "/daily",
    "introduction": "/intro",
    "chat": "/chat",
}


# Pydantic models for /chat
class ChatRequest(BaseModel):
    """Request body for /chat endpoint."""

    message: str
    speak: bool = False


class ChatResponse(BaseModel):
    """Response body for /chat endpoint."""

    response: str
    data: dict | None = None
    status: int


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
    """Run daily routine: fetch weather, calendar events, and todos, speak summary aloud."""
    # Get today's date
    today = datetime.date.today()
    today_iso = today.isoformat()
    today_formatted = today.strftime("%A, %B %d")  # e.g., "Sunday, December 08"

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
    events_res = await arms.get_events(today_iso)
    if events_res["status"] == 200 and events_res["result"]:
        events = json.loads(events_res["result"])
        vitals.info(f"Today's events: {len(events)} events found")
    else:
        events = []
        vitals.warning("Could not fetch calendar events")

    # Fetch todos
    todos_res = await arms.get_todos(today_iso)
    if todos_res["status"] == 200 and todos_res["result"]:
        todos = json.loads(todos_res["result"])
        vitals.info(f"Today's todos: {len(todos)} task(s) found")
    else:
        todos = []
        vitals.warning("Could not fetch todos")

    # Build consolidated data for a single AI prompt
    daily_data = {
        "date": today_formatted,
        "weather": weather,
        "calendar_events": events,
        "todos": todos,
    }

    # Generate a unified, intelligent daily briefing
    daily_prompt = f"""You are Nova, a personal AI assistant delivering a morning briefing for {today_formatted}.

Given the following data, create a natural, conversational daily briefing that flows smoothly as a single cohesive message. Do NOT simply list every item - instead, intelligently summarize and prioritize.

GUIDELINES:
1. Start with a brief, friendly greeting mentioning the day
2. Give a quick weather overview (temperature, conditions, anything notable like rain)
3. Highlight the 2-3 most important calendar events or meetings, mentioning approximate times
4. Mention 1-3 priority tasks from the todo list that are most actionable today
5. End with a brief, encouraging sign-off

CONSTRAINTS:
- Keep the entire briefing under 150 words
- Use natural speech patterns (e.g., "You've got a meeting at 10" not "Meeting scheduled for 10:00:00")
- Skip items that are routine/unimportant
- If there are no events or todos, briefly acknowledge it and move on
- Output plain text ONLY - no markdown, asterisks, bullet points, or formatting
- This will be read aloud by text-to-speech

DATA:
{json.dumps(daily_data, indent=2, default=str)}

Generate the daily briefing now:"""

    briefing = brain.process(daily_data, request_type="api_data", context=daily_prompt)

    # Generate audio from the briefing
    if briefing:
        mouth.speak(briefing)

    # Return full response including the AI-generated briefing
    return {
        "weather": weather,
        "events": events,
        "todos": todos,
        "briefing": briefing,
        "status": 200,
    }


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


@app.get("/todos")
async def get_todos():
    """Get today's tasks from Todoist."""
    today = datetime.date.today().isoformat()

    todos_res = await arms.get_todos(today)

    # Check if the API call was successful
    api_status_code = todos_res["status"]
    if api_status_code != 200:
        vitals.error(f"Error fetching todos: {api_status_code}")
        return None

    # Parse and return the todos
    todos = json.loads(todos_res["result"]) if todos_res["result"] else []
    vitals.info(f"Today's todos: {todos}")

    return todos


@app.get("/intro")
async def get_introduction():
    """Get AI-generated assistant introduction."""
    # Include today's date in the introduction
    today = datetime.date.today()

    prompt = (
        "Your name is Nova, a personal virtual assistant. "
        "Give me a brief introduction to yourself in less than 30 words. "
        "Feel free to incorporate the following information (today): "
        "IMPORTANT: Output plain text only - no markdown or formatting."
    )
    intro = brain.process(today, request_type="api_data", context=prompt)
    mouth.speak(intro)

    # Return the AI-generated introduction
    return {"intro": intro, "status": 200}


@app.post("/chat", response_model=ChatResponse)
async def chat_with_nova(request: ChatRequest) -> ChatResponse:
    """Handle conversational messages with Nova.

    Supports multi-turn conversations with memory, cached data access,
    and optional text-to-speech output.
    """
    user_message = request.message
    today = datetime.date.today().isoformat()

    vitals.info(f"Chat: {user_message[:50]}...")

    # Detect intents using hybrid detector
    intents = intent_detector.detect(user_message)
    force_refresh = Intent.REFRESH in intents
    fetched_data: dict = {}

    # Fetch data based on intents
    if Intent.WEATHER in intents:
        weather_data = await cache.get(
            "weather",
            arms.get_weather,
            force_refresh=force_refresh,
        )
        if weather_data and weather_data.get("result"):
            fetched_data["weather"] = json.loads(weather_data["result"])

    if Intent.EVENTS in intents:

        async def fetch_events():
            return await arms.get_events(today)

        events_data = await cache.get("events", fetch_events, force_refresh=force_refresh)
        if events_data and events_data.get("result"):
            fetched_data["events"] = json.loads(events_data["result"])

    if Intent.TODOS in intents:

        async def fetch_todos():
            return await arms.get_todos(today)

        todos_data = await cache.get("todos", fetch_todos, force_refresh=force_refresh)
        if todos_data and todos_data.get("result"):
            fetched_data["todos"] = json.loads(todos_data["result"])

    # Build complete system prompt (identity + data context)
    # Start with base system prompt (no data context yet)
    system_prompt = context_mgr.build_system_prompt(include_data_context=True)

    # Add freshly fetched data to system prompt
    if fetched_data:
        system_prompt += (
            f"\n\nFRESHLY FETCHED DATA:\n{json.dumps(fetched_data, indent=2, default=str)}"
        )

    # Get conversation history
    history = memory.get_for_context(hours=4.0, max_messages=30)

    # Generate AI response
    response_text = brain.chat(user_message, history=history, system_prompt=system_prompt)

    # Store messages in memory
    memory.add_message("user", user_message)
    memory.add_message("assistant", response_text)

    # Optional TTS
    if request.speak:
        mouth.speak(response_text)

    vitals.info(f"Response: {response_text[:50]}...")

    return ChatResponse(
        response=response_text,
        data=fetched_data if fetched_data else None,
        status=200,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(f"{__name__}:app", host="127.0.0.1", port=8000)
