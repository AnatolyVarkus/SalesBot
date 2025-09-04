from dataclasses import dataclass
from dotenv import load_dotenv
import os
load_dotenv()

@dataclass
class Credentials:
    # Open AI
    OPEN_AI_API_KEY: str = os.environ.get("OPEN_AI_API_KEY")

    # Telegram API Parameters
    API_ID: int = int(os.environ.get("API_ID"))
    API_HASH: str = os.environ.get("API_HASH")
    SESSION_NAME: str = 'SalesBot'

@dataclass
class Settings:
    # Настройки чата
    CHAT_STATES = {}
    DEBOUNCE_SECONDS = 3  # ждать после окончания печати
    MIN_IN_CHAT_TIME = 30  # оставаться в чате после последнего сообщения
    ENTER_MIN = 10  # мин время до входа в чат, если не в чате
    ENTER_MAX = 30

credentials = Credentials()
settings = Settings()