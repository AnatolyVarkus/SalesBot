from openai import AsyncOpenAI
from app.general import credentials
from app.behaviour import ai_prompts
from openai.types.responses.response_text_config_param import ResponseTextConfigParam
from typing_extensions import TypedDict, Literal
from openai.types.shared_params.response_format_json_object import ResponseFormatJSONObject
from app.bot.image_handler import _sniff_mime, download_image_as_data_url, is_image

class OpenAIClient:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=credentials.OPEN_AI_API_KEY)

    async def generate_response(self, history, sender_name, client):
        prompt = ai_prompts.generate_system_prompt(sender_name)
        messages = [{"role": "system", "content": prompt}]

        for msg in reversed(history):
            # print(msg.stringify())
            if is_image(msg):
                data_url = await download_image_as_data_url(msg)
                role = 'assistant' if msg.out else 'user'
                message = msg.message if msg.message else ""
                messages.append({"role": role, "content": [{"type": "input_image", "image_url": data_url},
                                                           {"type": "input_text", "text": message}]})
                continue
            elif msg.message is None:
                continue
            role = 'assistant' if msg.out else 'user'
            content = f"{msg.message} [message_id={msg.id}]"
            messages.append({"role": role, "content": content})

        print(f"Messages history: {messages}")

        return await self.send_open_ai_request(messages)


    async def send_open_ai_request(self, messages):
        response = await self.client.responses.create(
            model="gpt-5",
            input=messages,
            text=ResponseTextConfigParam(format=ResponseFormatJSONObject(type="json_object")),
            reasoning = {"effort": "low"}
        )

        print(f"Open AI response: {response.output_text.strip()}")
        return response.output_text.strip().replace(" )", ")")

open_ai_client = OpenAIClient()

a = {
    "tool": "multiple_replies",
    "messages": [
        {
            "type": "direct_reply",
            "to_msg": 123123,
            "message": "Hello"
        },
        {
            "type": "indirect_reply",
            "message": "Hi"
        }
    ]
}

b = {
    "tool": "singular_reply",
    "message": {
        "type": "direct_reply",
        "to_msg": 123123,
        "message": "Hello"
    }
}

