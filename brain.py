# TODO - import openai tool
# import openai


class SampleAI:
    def __init__(self):
        self.do_something = lambda x: x


class Brain:
    def __init__(self):
        # self.ai = openai.start()  # TODO - Just an example init
        self.ai = SampleAI()

    def process(self, message, request_type) -> str:
        if request_type == "speech":
            output = self.ai.do_something(message)
        else:
            output = "Hello world!"

        return output
