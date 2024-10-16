import os
import google.generativeai as genai
import json
from prompts import BASE_PROMPT, CONVO_WRAPPER

with open('config.json') as f:
    config = json.load(f)
# Get the API key from the config
genai.configure(api_key=config['GEMINI_API_KEY'])


class Ai_Helper:
    def __init__(self):
        self.generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro-002",
            generation_config=self.generation_config,
            # safety_settings = Adjust safety settings
            # See https://ai.google.dev/gemini-api/docs/safety-settings
            system_instruction=BASE_PROMPT
        )
        self.history = []
        self.chat_session = self.model.start_chat(history=self.history)

    def update_convo(self, msg_queue):
        self.history = [{'role': 'user',
                         'parts': [CONVO_WRAPPER.format(convo=f"""{json.dumps(msg_queue)}""")]
                         }]
        self.chat_session = self.model.start_chat(history=self.history)

    def ask_q(self, q):
        return self.chat_session.send_message(q).text
