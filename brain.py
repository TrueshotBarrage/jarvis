import logging
from typing import List, Dict

import google.api_core.exceptions
import google.generativeai as genai
import json


class Brain:
    def __init__(self, secrets_file="secrets.json"):
        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Read the secrets.json file with the json library, then extract the key
        self.logger.info("Reading secrets from config...")
        with open(secrets_file, "r") as f:
            secrets = json.load(f)
        gemini_api_key = secrets["gemini_api_key"]
        self.logger.info("Secrets fully initialized.")

        # Initialize the AI
        self.logger.info("Establishing handshake protocol with Gemini...")
        genai.configure(api_key=gemini_api_key)
        self.ai = genai.GenerativeModel("gemini-1.5-flash")
        try:
            conn_test_res = self.ai.generate_content(
                "Test!", request_options={"timeout": 10}
            )
            conn_success = conn_test_res.text
            self.logger.info(conn_success)
            self.logger.info("Contact established with Gemini servers.")
        except google.api_core.exceptions.DeadlineExceeded as e:
            self.logger.warning(f"Gemini timeout error: {e}")
            self.logger.warning(
                "Error establishing handshake with Gemini servers. Check your connection to the multiverse grid?"
            )
            conn_success = None

        if conn_success:
            self.logger.info("Intelligence cortex fully activated and ready to go!")
        else:
            self.logger.info(
                "Intelligence cortex activated, but cannot reach multiverse grid network. "
                "Complex thought processing may not be available."
            )

    def process(self, message, request_type, context) -> str:
        if request_type == "api_data":
            prompt = f"{context}\n{message}" if context is not None else message
            thought = self.ai.generate_content(prompt)
            output = thought.text
        elif request_type == "choose":
            prompt = (
                f"The user is saying: '{message}'. Based on this input, choose "
                f"the most likely option that the user is suggesting from the following options: "
                f"{context}"
            )
            thought = self.ai.generate_content(prompt)
            output = thought.text
        elif request_type == "choose_distribution":
            prompt = (
                f"The user is saying: '{message}'. Based on this input, provide a normalized "
                f"probability distribution of the likelihood of each option that the user is suggesting "
                f"from the following options: "
                f"{context}"
                f"\nFormat the output as a JSON object with the keys being the options and the values being the "
                f"probability of that option, with the keys sorted in descending order of probability. "
                f"For example: '{'Option 1': 0.5, 'Option 2': 0.3, 'Option 3': 0.2}'."
            )
            thought = self.ai.generate_content(prompt)
            output = thought.text
        else:
            output = "Hello world!"

        return output

    def choose(
        self, user_input: str, options: List[str], get_probabilities: bool = False
    ) -> str | Dict[str, float]:
        choose_type = "choose_distribution" if get_probabilities else "choose"
        likely_option = self.process(user_input, choose_type, options)
        if get_probabilities:
            likely_option = json.loads(likely_option)

        return likely_option
