from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class ApplicationSettings:
    database_path: Path
    telegram_bot_token: str


def load_application_settings() -> ApplicationSettings:
    load_dotenv()
    database_path_value = os.getenv("DATABASE_PATH", "data/personal_bot.sqlite3")
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

    if not telegram_bot_token:
        raise ValueError("У .env потрібно вказати TELEGRAM_BOT_TOKEN.")

    return ApplicationSettings(
        database_path=Path(database_path_value),
        telegram_bot_token=telegram_bot_token,
    )
