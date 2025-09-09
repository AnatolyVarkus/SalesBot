import os
import random
import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import SendMessageTypingAction
from telethon import errors
import json
from app.general import credentials, settings
from .chat_state import ChatState
from app.behaviour import ai_prompts
from app.services import open_ai_client
from .time_handler import bot_can_answer, seconds_until_can_answer

class BotHandler:
    def __init__(self):
        self.client = TelegramClient(credentials.SESSION_NAME, credentials.API_ID, credentials.API_HASH,
                                     system_version="4.16.30-vxCUSTOM", device_model="iphone")
        self.chat_states = {}
        self.client.add_event_handler(self.on_new_message,
                                      events.NewMessage(incoming=True))
        self.client.add_event_handler(self.on_user_update,
                                      events.UserUpdate())

    async def debounce_and_send(self, chat_id, sender_name):
        state = self.chat_states[chat_id]

        while state.last_typing_time and (asyncio.get_event_loop().time() - state.last_typing_time) < 8:
            await asyncio.sleep(0.5)

        await asyncio.sleep(settings.DEBOUNCE_SECONDS)

        await self.send_reply(chat_id, sender_name)
        state.last_msg_time = asyncio.get_event_loop().time()

    async def send_reply(self, chat_id, sender_name):
        print(f"Starting to send reply to {chat_id}")
        history = await self.client.get_messages(chat_id, limit=100)
        reply = await open_ai_client.generate_response(history, sender_name, self.client)
        messages = json.loads(reply)["messages"]
        for message in messages:
            async with self.client.action(chat_id, 'typing'):
                await asyncio.sleep(len(message[0]) / random.uniform(6, 8))
            if len(message) == 1:
                await self.client.send_message(chat_id, message[0])
                self.chat_states[chat_id].last_msg_time = asyncio.get_event_loop().time()
                self.chat_states[chat_id].in_chat = True
                await asyncio.sleep(random.uniform(0, 1))
            else:
                await self.client.send_message(chat_id, message[0], reply_to=int(message[1]))
                self.chat_states[chat_id].last_msg_time = asyncio.get_event_loop().time()
                self.chat_states[chat_id].in_chat = True
                await asyncio.sleep(random.uniform(0, 1))

    async def handle_message(self, event):
        if not event.is_private:
            return
        chat_id = event.chat_id

        sender = await event.get_sender()
        first_name = (sender.first_name or "").strip()
        last_name = (sender.last_name or "").strip()
        sender_name = (first_name + " " + last_name).strip()
        # print(f"{sender_name = }")

        if chat_id not in self.chat_states:
            self.chat_states[chat_id] = ChatState()
        state = self.chat_states[chat_id]

        now = asyncio.get_event_loop().time()

        if not state.in_chat:
            if not bot_can_answer():
                await asyncio.sleep(float(seconds_until_can_answer()+random.uniform(settings.ENTER_MIN, settings.ENTER_MAX*10)))
            wait = random.uniform(settings.ENTER_MIN, settings.ENTER_MAX)
            # print(f"Waiting {wait} seconds")
            await asyncio.sleep(wait)
            state.in_chat = True
            state.first_msg_time = now

        await event.mark_read()

        state.last_msg_time = now

        if state.debounce_task and not state.debounce_task.done():
            state.debounce_task.cancel()

        state.debounce_task = asyncio.create_task(self.debounce_and_send(chat_id, sender_name))

    async def monitor_exits(self):
        while True:
            now = asyncio.get_event_loop().time()
            for chat_id, state in list(self.chat_states.items()):
                if state.in_chat and (now - state.last_msg_time) > settings.MIN_IN_CHAT_TIME:
                    state.in_chat = False
                    # if state.debounce_task:
                    #     state.debounce_task.cancel()
            await asyncio.sleep(5)

    async def process_unanswered_messages(self):
        dialogs = await self.client.get_dialogs()
        for dialog in dialogs:

            if not dialog.is_user or dialog.entity.bot:
                continue
            chat_id = dialog.id
            if chat_id in settings.PROHIBITED_IDS:
                continue
            messages = await self.client.get_messages(chat_id, limit=1)
            if not messages:
                continue
            last_msg = messages[0]
            # print(f"{last_msg.message = }")
            if last_msg.out or last_msg.message is None:
                continue
            await self.client.send_read_acknowledge(chat_id)

            if chat_id not in self.chat_states:
                self.chat_states[chat_id] = ChatState()
            state = self.chat_states[chat_id]
            if not state.in_chat:
                state.in_chat = True
                state.first_msg_time = asyncio.get_event_loop().time()
            state.last_msg_time = asyncio.get_event_loop().time()
            await self.send_reply(chat_id, "")

    async def on_new_message(self, event):
        await self.handle_message(event)

    async def on_user_update(self, event):

        action = getattr(event, 'action', None)
        if event.is_private and isinstance(action, SendMessageTypingAction):
            chat_id = event.chat_id
            if chat_id in self.chat_states:
                self.chat_states[chat_id].last_typing_time = asyncio.get_event_loop().time()


bot_handler = BotHandler()




