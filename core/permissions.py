from __future__ import annotations

import os

DEFAULT_OWNER_ID = 176308213489205249


def owner_id() -> int:
    raw = os.getenv("BOT_OWNER_ID", str(DEFAULT_OWNER_ID)).strip()
    try:
        return int(raw)
    except ValueError:
        return DEFAULT_OWNER_ID


def is_developer(user_id: int) -> bool:
    return int(user_id) == owner_id()
