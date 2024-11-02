import google.generativeai as genai
import json


class Brain:
    def __init__(self, secrets_file="secrets.json"):
        # Read the secrets.json file with the json library, then extract the key
        with open(secrets_file, "r") as f:
            secrets = json.load(f)
        gemini_api_key = secrets["gemini_api_key"]

        # Initialize the AI
        genai.configure(api_key=gemini_api_key)
        self.ai = genai.GenerativeModel("gemini-1.5-flash")

    def process(self, message, request_type, context) -> str:
        if request_type == "speech":
            prompt = f"{context}\n{message}" if context is not None else message
            thought = self.ai.generate_content(prompt)
            output = thought.text
        else:
            output = "Hello world!"

        return output
