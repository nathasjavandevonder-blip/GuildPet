from __future__ import annotations

import json
from typing import Any

from core.database import db_session
from core.events.models import DomainEvent


NOTIFICATION_EVENTS = {
    "combat.won": (
        "combat_reward",
        "Combat Victory",
    ),
    "combat.lost": (
        "combat_result",
        "Combat Defeat",
    ),
    "adventure.completed": (
        "adventure_reward",
        "Adventure Complete",
    ),
    "achievement.unlocked": (
        "achievement",
        "Achievement Unlocked",
    ),
    "world.weather_changed": (
        "world",
        "Weather Changed",
    ),
}


def _description_for(
    event: DomainEvent,
) -> str:
    payload = event.payload

    if event.event_type == "combat.won":
        enemy = payload.get("enemy_name", "an enemy")
        xp = payload.get("xp", 0)
        tokens = payload.get("tokens", 0)

        return (
            f"The dragon defeated **{enemy}** and earned "
            f"**{xp} XP** and **{tokens} tokens**."
        )

    if event.event_type == "adventure.completed":
        adventure = payload.get(
            "adventure_name",
            "an adventure",
        )

        return (
            f"The dragon safely completed "
            f"**{adventure}**."
        )

    if event.event_type == "achievement.unlocked":
        name = payload.get(
            "achievement_name",
            payload.get("achievement_key", "Unknown"),
        )

        return f"**{name}** was unlocked."

    if event.event_type == "world.weather_changed":
        weather = payload.get("weather_name", "Unknown")

        return f"The weather is now **{weather}**."

    return str(
        payload.get(
            "description",
            event.event_type,
        )
    )


async def notification_listener(
    event: DomainEvent,
) -> None:
    notification = NOTIFICATION_EVENTS.get(
        event.event_type
    )

    if notification is None:
        return

    notification_type, title = notification

    with db_session() as connection:
        connection.execute(
            """
            INSERT INTO guild_notifications_v5 (
                guild_id,
                event_id,
                notification_type,
                title,
                description,
                metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event.guild_id,
                event.event_id,
                notification_type,
                title,
                _description_for(event),
                json.dumps(
                    event.payload,
                    separators=(",", ":"),
                    ensure_ascii=False,
                    default=str,
                ),
            ),
        )


def get_pending_notifications(
    guild_id: int,
    *,
    limit: int = 20,
):
    with db_session() as connection:
        return connection.execute(
            """
            SELECT *
            FROM guild_notifications_v5
            WHERE guild_id = ?
              AND delivered = 0
            ORDER BY id ASC
            LIMIT ?
            """,
            (
                guild_id,
                limit,
            ),
        ).fetchall()


def mark_notifications_delivered(
    notification_ids: list[int],
) -> None:
    if not notification_ids:
        return

    placeholders = ",".join(
        "?" for _ in notification_ids
    )

    with db_session() as connection:
        connection.execute(
            f"""
            UPDATE guild_notifications_v5
            SET delivered = 1,
                delivered_at = CURRENT_TIMESTAMP
            WHERE id IN ({placeholders})
            """,
            notification_ids,
        )
