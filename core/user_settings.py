from __future__ import annotations

from core.database import db_session
from core.i18n import DEFAULT_LOCALE, available_languages, LocalizationService


def normalize_supported_language(language: str | None) -> str:
    normalized = LocalizationService.normalize_locale(language)
    supported = set(available_languages())

    if normalized in supported:
        return normalized

    if "-" in normalized:
        language_only = normalized.split("-", 1)[0]
        if language_only in supported:
            return language_only

    return DEFAULT_LOCALE


def get_language(user_id: int) -> str:
    with db_session() as connection:
        row = connection.execute(
            """
            SELECT language
            FROM user_settings_v55
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

    if row is None:
        return DEFAULT_LOCALE

    return normalize_supported_language(row["language"])


def set_language(user_id: int, language: str) -> str:
    normalized = normalize_supported_language(language)

    with db_session() as connection:
        connection.execute(
            """
            INSERT INTO user_settings_v55 (
                user_id,
                language
            )
            VALUES (?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET
                language = excluded.language,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, normalized),
        )

    return normalized


def get_or_create_language(
    user_id: int,
    discord_locale: str | None = None,
) -> str:
    with db_session() as connection:
        row = connection.execute(
            """
            SELECT language
            FROM user_settings_v55
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

        if row is not None:
            return normalize_supported_language(row["language"])

        language = normalize_supported_language(discord_locale)

        connection.execute(
            """
            INSERT INTO user_settings_v55 (
                user_id,
                language
            )
            VALUES (?, ?)
            """,
            (user_id, language),
        )

    return language
