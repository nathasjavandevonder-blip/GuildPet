from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    database_path: Path
    temporary_message_seconds: int
    channel_message_minutes: int
    adventure_message_minutes: int
    event_claim_minutes: int


def load_settings() -> Settings:
    default_database = BASE_DIR / "guild_dragon_v5_test.db"

    database_path = Path(
        os.getenv("GUILDPET_DB_FILE", str(default_database))
    ).expanduser()

    if not database_path.is_absolute():
        database_path = BASE_DIR / database_path

    return Settings(
        database_path=database_path,
        temporary_message_seconds=int(
            os.getenv("TEMP_MESSAGE_SECONDS", "30")
        ),
        channel_message_minutes=int(
            os.getenv("CHANNEL_MESSAGE_MINUTES", "30")
        ),
        adventure_message_minutes=int(
            os.getenv("ADVENTURE_MESSAGE_MINUTES", "30")
        ),
        event_claim_minutes=int(
            os.getenv("EVENT_CLAIM_MINUTES", "15")
        ),
    )


settings = load_settings()
