import logging
import threading

from gtts import gTTS
import playsound
import pydub

from brain import Brain  # Just for type inferences


class Mouth:
    def __init__(self, brain: Brain):
        # Set up logging
        self.logger = logging.getLogger(__name__)

        self.brain = brain

        self.logger.info("Voice protocol ready. Sound systems operational!")

    def speak(self, blurb) -> None:
        # Create a temporary audio file
        sound_file = "speech.mp3"
        gTTS(blurb, slow=False).save(sound_file)
        self.logger.info(f"Saved {sound_file}")

        # Speed up the audio file because the default voice library output speaks like a snail
        self.speed_up(sound_file, playback_speed=1.25)

        # Directly play the audio file
        threading.Thread(
            target=playsound.playsound, args=(sound_file,), daemon=True
        ).start()

    @staticmethod
    def speed_up(sound_file, playback_speed) -> None:
        sound = pydub.AudioSegment.from_file(sound_file)
        faster_sound = sound.speedup(playback_speed=playback_speed)
        faster_sound.export(sound_file, format="mp3")
