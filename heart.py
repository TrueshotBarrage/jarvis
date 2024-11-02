import json

from brain import Brain
from arms import Arms
from mouth import Mouth

import datetime
import logging

from fastapi import FastAPI
from contextlib import asynccontextmanager


def become_intelligent():
    vitals.info("[Brain] Becoming intelligent...")
    return Brain()


def attach_arms():
    vitals.info("[Arms] Attaching useful appendages...")
    return Arms()


def unmute():
    vitals.info("[Mouth] Un-muting...")
    return Mouth(brain)


logging.basicConfig(
    level=logging.INFO, format="%(levelname)-9s %(asctime)s - %(name)s - %(message)s"
)
vitals = logging.getLogger("Jarvis")

vitals.info("[Heart] Coming to life...")
brain = become_intelligent()
arms = attach_arms()
mouth = unmute()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    arms.start()
    # Run the application
    yield
    # On shutdown
    await arms.stop()


app = FastAPI(lifespan=lifespan)


@app.get("/test-call-external")
async def call_external_api(url: str = "https://stackoverflow.com"):
    res = await arms.get(url)
    vitals.info(f"External API response: {res["status"]}")
    return res


@app.get("/daily")
async def run_daily_routine():
    # Fetch today's weather, todos, and calendar events
    today = datetime.date.today()

    # Invoke the weather API
    weather_res = await arms.get_weather()

    # Check if the API call was successful
    api_status_code = weather_res["status"]
    if api_status_code != 200:
        vitals.error(f"Error fetching weather: {api_status_code}")
        return

    # Parse the weather data
    weather = weather_res["result"] = json.loads(weather_res["result"])

    # Output the weather
    vitals.info(f"Today's weather: {weather}")

    # todos_today = await client.get_todos(today)
    # events_today = await client.get_events(today)

    # In the beginning was the Word! - These are side effects

    # Example weather API response:
    # {"result":{"latitude":40.78858,"longitude":-73.96611,"generationtime_ms":0.07402896881103516,"utc_offset_seconds":-14400,"timezone":"America/New_York","timezone_abbreviation":"EDT","elevation":45.0,"current_units":{"time":"iso8601","interval":"seconds","temperature_2m":"°F","precipitation":"mm"},"current":{"time":"2024-10-31T01:00","interval":900,"temperature_2m":60.7,"precipitation":0.0},"daily_units":{"time":"iso8601","temperature_2m_max":"°F","temperature_2m_min":"°F","sunrise":"iso8601","sunset":"iso8601","precipitation_hours":"h"},"daily":{"time":["2024-10-31","2024-11-01","2024-11-02","2024-11-03","2024-11-04","2024-11-05","2024-11-06"],"temperature_2m_max":[81.4,76.0,60.4,60.1,55.1,58.4,74.9],"temperature_2m_min":[54.3,54.2,47.7,48.6,50.7,49.9,58.7],"sunrise":["2024-10-31T07:26","2024-11-01T07:27","2024-11-02T07:28","2024-11-03T07:29","2024-11-04T07:30","2024-11-05T07:31","2024-11-06T07:33"],"sunset":["2024-10-31T17:52","2024-11-01T17:51","2024-11-02T17:50","2024-11-03T17:49","2024-11-04T17:48","2024-11-05T17:46","2024-11-06T17:45"],"precipitation_hours":[0.0,0.0,0.0,1.0,2.0,12.0,0.0]}},"status":200}
    weather_prompt_context = (
        "Given the weather API response data, generate a concise and engaging "
        "message suitable for a personal assistant to read aloud. The message should "
        "include current temperature, chance of rain, and any notable weather events "
        "for today. Include a brief description of the highs and lows of the daily "
        "weather, if it exists, as well as sunrise and sunset times. "
        "Ensure the message is friendly and easy to understand."
    )
    mouth.speak(weather, context=weather_prompt_context)

    # mouth.speak(todos_today)
    # mouth.speak(events_today)

    # Return a response
    return weather_res


@app.get("/test")
async def test():
    # Fetch today's weather, todos, and calendar events
    today = datetime.date.today()

    prompt = (
        "Your name is Nova, a personal virtual assistant. "
        "Give me a brief introduction to yourself in less than 30 words."
        "Feel free to incorporate the following information (today):"
    )
    mouth.speak(today, context=prompt)

    # Return a response
    return {"result": "Test API response", "status": 200}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(f"{__name__}:app", host="127.0.0.1", port=8000)
