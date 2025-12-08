"""Tests for the Mouth (TTS) module."""

from unittest.mock import MagicMock, patch

from mouth import DEFAULT_AUDIO_FILE, Mouth


class TestMouth:
    """Test suite for Mouth TTS module."""

    def test_default_initialization(self):
        """Test Mouth initializes with default audio file."""
        mouth = Mouth()
        assert mouth.audio_file == DEFAULT_AUDIO_FILE

    def test_custom_audio_file(self):
        """Test Mouth can be initialized with custom audio file path."""
        mouth = Mouth(audio_file="/tmp/custom.mp3")
        assert mouth.audio_file == "/tmp/custom.mp3"

    @patch("mouth.playsound.playsound")
    @patch("mouth.pydub.AudioSegment")
    @patch("mouth.gTTS")
    def test_speak_creates_audio_file(self, mock_gtts, mock_audio, _mock_playsound):
        """Test speak() creates and plays audio file."""
        # Setup mocks
        mock_tts_instance = MagicMock()
        mock_gtts.return_value = mock_tts_instance

        mock_sound = MagicMock()
        mock_audio.from_file.return_value = mock_sound
        mock_sound.speedup.return_value = mock_sound

        mouth = Mouth(audio_file="/tmp/test.mp3")
        mouth.speak("Hello world")

        # Verify gTTS was called
        mock_gtts.assert_called_once_with("Hello world", slow=False)
        mock_tts_instance.save.assert_called_once_with("/tmp/test.mp3")

    @patch("mouth.pydub.AudioSegment")
    def test_speed_up_modifies_audio(self, mock_audio):
        """Test _speed_up modifies playback speed."""
        mock_sound = MagicMock()
        mock_audio.from_file.return_value = mock_sound
        mock_faster = MagicMock()
        mock_sound.speedup.return_value = mock_faster

        Mouth._speed_up("/tmp/test.mp3", 1.5)

        mock_audio.from_file.assert_called_once_with("/tmp/test.mp3")
        mock_sound.speedup.assert_called_once_with(playback_speed=1.5)
        mock_faster.export.assert_called_once_with("/tmp/test.mp3", format="mp3")

    @patch("mouth.playsound.playsound")
    @patch("mouth.pydub.AudioSegment")
    @patch("mouth.gTTS")
    def test_speak_custom_playback_speed(self, mock_gtts, mock_audio, _mock_playsound):
        """Test speak() respects custom playback speed."""
        mock_tts_instance = MagicMock()
        mock_gtts.return_value = mock_tts_instance

        mock_sound = MagicMock()
        mock_audio.from_file.return_value = mock_sound
        mock_sound.speedup.return_value = mock_sound

        mouth = Mouth()
        mouth.speak("Test", playback_speed=1.5)

        mock_sound.speedup.assert_called_once_with(playback_speed=1.5)
