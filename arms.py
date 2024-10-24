# import axios - TODO: Proper API call lib import


class SampleAPI:
    def __init__(self):
        self.get = lambda s: f"[Request to URL: {s}]"


class ArmReachFailure(Exception):
    def __init__(self, e):
        raise Exception(
            f"""
[!] Arms could not reach a proper response.
[Execution trace]
{e}
"""
        )


class Arms:
    def __init__(self):
        # self.api = axios.init()  # TODO - initialize with external API call tool
        self.api = SampleAPI()

    async def get(self, url):
        res = await self.api.get(url)
        if res:
            return res.body
        raise ArmReachFailure(res.error)

    async def get_weather(self, day):
        weather_url = f"/route/to/weather/api/{day}"
        weather = await self.get(weather_url)

        return weather

    async def get_todos(self, day):
        todoist_url = f"/route/to/todoist/api/{day}"
        todos = await self.get(todoist_url)

        return todos

    async def get_events(self, day):
        gcal_url = f"/route/to/gcal/api/{day}"
        events = await self.get(gcal_url)

        return events
