import logging
import threading

from gtts import gTTS
import playsound

from brain import Brain  # Just for type inferences

logger = logging.getLogger(__name__)


class SampleSpeaker:
    def __init__(self):
        self.blurb = print


class Mouth:
    def __init__(self, brain: Brain):
        self.brain = brain
        # self.speaker = vocal_lib.init()  # TODO - example vocal unit init
        self.speaker = SampleSpeaker()

    def speak(self, message, context=None) -> None:
        # Process the message using the brain
        vocal_output = self.brain.process(
            message, request_type="speech", context=context
        )

        # TODO - some API to make physical sound
        self.speaker.blurb(vocal_output)

        logger.info(f"Saved speech.mp3")
        gTTS(vocal_output, slow=False).save("speech.mp3")

        # Directly play the audio file
        threading.Thread(
            target=playsound.playsound, args=("speech.mp3",), daemon=True
        ).start()
