from brain import Brain
from arms import Arms
from mouth import Mouth

import datetime
import logging


class Heart:
    def __init__(self, logger=None):
        self.vitals = logger if logger else logging.getLogger()
        self.brain = self.become_intelligent()
        self.arms = self.attach_arms()
        self.mouth = self.unmute()

    def become_intelligent(self):
        self.vitals.info("[Brain] Becoming intelligent...")
        return Brain()

    def attach_arms(self):
        self.vitals.info("[Arms] Attaching useful appendages...")
        return Arms()

    def unmute(self):
        self.vitals.info("[Mouth] Becoming unmute...")
        return Mouth(self.brain)

    async def run_daily_routine(self):
        # Fetch today's weather, todos, and calendar events
        today = datetime.date.today()
        weather_today = await self.arms.get_weather(today)
        todos_today = await self.arms.get_todos(today)
        events_today = await self.arms.get_events(today)

        # In the beginning was the Word! - These are side effects
        self.mouth.speak(weather_today)
        self.mouth.speak(todos_today)
        self.mouth.speak(events_today)
