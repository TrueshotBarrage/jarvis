# import vocal_lib

from brain import Brain  # Just for type inferences


class SampleSpeaker:
    def __init__(self):
        self.blurb = print


class Mouth:
    def __init__(self, brain: Brain):
        self.brain = brain
        # self.speaker = vocal_lib.init()  # TODO - example vocal unit init
        self.speaker = SampleSpeaker()

    def speak(self, message) -> None:
        vocal_output = self.brain.process(message, request_type="speech")

        # TODO - some API to make physical sound
        self.speaker.blurb(vocal_output)
