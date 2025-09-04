from dataclasses import dataclass

@dataclass
class ChatState:
    in_chat = False
    first_msg_time = None
    last_msg_time = None
    debounce_task = None
    last_typing_time = None