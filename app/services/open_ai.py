from openai import OpenAI
from app.general import credentials
from app.behaviour import ai_prompts

class OpenAIClient:
    def __init__(self):
        self.client = OpenAI(api_key=credentials.OPEN_AI_API_KEY)
        self.system_prompt = ai_prompts.system_prompt

    def generate_response(self, history, system_prompt = None):
        messages = [{"role": "system", "content": system_prompt if system_prompt else self.system_prompt}]

        for msg in reversed(history):
            if msg.message is None:
                continue
            role = 'assistant' if msg.out else 'user'
            messages.append({"role": role, "content": msg.message})

        return self.send_open_ai_request(messages)

    def send_open_ai_request(self, messages):
        response = self.client.responses.create(
            model="gpt-5",
            input=messages
        )
        return response.output_text.strip()

open_ai_client = OpenAIClient()

