from __future__ import annotations

from core.database import db_session
from core.dragon_status import DragonStatus, load_dragon_status


class DragonService:
    """Application layer used by UI and future gameplay systems.

    Sprint 1 intentionally keeps existing gameplay services intact. New actions
    should be added here instead of putting database or gameplay logic in views.
    """

    def status(self, guild_id: int) -> DragonStatus:
        return load_dragon_status(guild_id)

    def record_activity(self, guild_id: int, text: str) -> None:
        clean = " ".join(text.split()).strip()
        if not clean:
            return

        with db_session() as connection:
            connection.execute(
                """
                INSERT INTO dashboard_activity_v5 (guild_id, activity_text)
                VALUES (?, ?)
                """,
                (guild_id, clean[:300]),
            )

            connection.execute(
                """
                DELETE FROM dashboard_activity_v5
                WHERE guild_id = ? AND id NOT IN (
                    SELECT id FROM dashboard_activity_v5
                    WHERE guild_id = ?
                    ORDER BY id DESC
                    LIMIT 25
                )
                """,
                (guild_id, guild_id),
            )


service = DragonService()
