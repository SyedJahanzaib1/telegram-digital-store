import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    telegram_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    aiverse_api_key: str = os.getenv("AIVERSEHUB_API_KEY", "AK_6m9BfNVrXNPat0F1JybPLxEo2mkfS3Fx")
    aiverse_base_url: str = os.getenv("AIVERSEHUB_BASE_URL", "https://aiversehub.store")
    profit_markup_percent: float = float(os.getenv("PROFIT_MARKUP_PERCENT", "20.0"))
    admin_chat_id: str = os.getenv("ADMIN_CHAT_ID", "6042459817")

config = Config()
