"""Mouth module - Text-to-speech output for Jarvis.

This module provides vocal output capabilities using Google Text-to-Speech (gTTS)
with audio speed adjustment and playback.
"""

import logging

import playsound3
import pydub
from gtts import gTTS

# Default audio output file path
DEFAULT_AUDIO_FILE = "speech.mp3"


class Mouth:
    """Text-to-speech output handler.

    Converts text to speech using gTTS and plays it through the system speakers.
    Audio is sped up from the default rate for more natural listening.

    Attributes:
        logger: Module logger instance.
        audio_file: Path to the audio output file.
    """

    def __init__(self, audio_file: str = DEFAULT_AUDIO_FILE) -> None:
        """Initialize the Mouth with audio configuration.

        Args:
            audio_file: Path where generated audio will be saved.
        """
        self.logger = logging.getLogger(__name__)
        self.audio_file = audio_file
        self.logger.info("Voice protocol ready. Sound systems operational!")

    def speak(self, blurb: str, playback_speed: float = 1.25) -> None:
        """Convert text to speech and play it aloud.

        Args:
            blurb: The text to speak.
            playback_speed: Speed multiplier for audio (default 1.25x).
        """
        # Generate audio file from text
        gTTS(blurb, slow=False).save(self.audio_file)
        self.logger.info(f"Saved {self.audio_file}")

        # Speed up audio (default gTTS speaks slowly)
        self._speed_up(self.audio_file, playback_speed=playback_speed)

        # Play audio synchronously (blocks until done)
        playsound3.playsound(self.audio_file)

    @staticmethod
    def _speed_up(sound_file: str, playback_speed: float) -> None:
        """Speed up an audio file by the given factor.

        Args:
            sound_file: Path to the audio file to modify.
            playback_speed: Speed multiplier (e.g., 1.25 = 25% faster).
        """
        sound = pydub.AudioSegment.from_file(sound_file)
        faster_sound = sound.speedup(playback_speed=playback_speed)
        faster_sound.export(sound_file, format="mp3")
