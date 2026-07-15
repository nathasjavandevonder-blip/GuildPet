from __future__ import annotations

from core.database import db_session
from core.i18n import DEFAULT_LOCALE
from core.user_settings import normalize_supported_language


def get_guild_language(guild_id: int) -> str:
    with db_session() as connection:
        row = connection.execute(
            """
            SELECT language
            FROM guild_settings_v55
            WHERE guild_id = ?
            """,
            (guild_id,),
        ).fetchone()

    if row is None:
        return DEFAULT_LOCALE

    return normalize_supported_language(row["language"])


def set_guild_language(guild_id: int, language: str) -> str:
    normalized = normalize_supported_language(language)

    with db_session() as connection:
        connection.execute(
            """
            INSERT INTO guild_settings_v55 (
                guild_id,
                language
            )
            VALUES (?, ?)
            ON CONFLICT(guild_id)
            DO UPDATE SET
                language = excluded.language,
                updated_at = CURRENT_TIMESTAMP
            """,
            (guild_id, normalized),
        )

    return normalized
