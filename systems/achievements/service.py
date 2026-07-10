from __future__ import annotations

from core.database import db_session
from systems.achievements.catalog import get_definition, load_catalog
from systems.achievements.models import AchievementProgress


def add_progress(
    guild_id: int,
    user_id: int,
    metric: str,
    amount: int = 1,
) -> list[str]:
    if amount <= 0:
        return []

    unlocked_now: list[str] = []

    for definition in load_catalog().values():
        if definition.metric != metric:
            continue

        with db_session() as connection:
            connection.execute(
                """
                INSERT INTO achievement_progress_v5 (
                    guild_id,
                    user_id,
                    achievement_key,
                    progress,
                    updated_at
                )
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT (guild_id, user_id, achievement_key)
                DO UPDATE SET
                    progress = progress + excluded.progress,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    guild_id,
                    user_id,
                    definition.key,
                    amount,
                ),
            )

            row = connection.execute(
                """
                SELECT progress, unlocked_at
                FROM achievement_progress_v5
                WHERE guild_id = ?
                  AND user_id = ?
                  AND achievement_key = ?
                """,
                (
                    guild_id,
                    user_id,
                    definition.key,
                ),
            ).fetchone()

            if (
                row is not None
                and row["unlocked_at"] is None
                and row["progress"] >= definition.target
            ):
                connection.execute(
                    """
                    UPDATE achievement_progress_v5
                    SET unlocked_at = CURRENT_TIMESTAMP
                    WHERE guild_id = ?
                      AND user_id = ?
                      AND achievement_key = ?
                    """,
                    (
                        guild_id,
                        user_id,
                        definition.key,
                    ),
                )
                unlocked_now.append(definition.key)

    return unlocked_now


def get_progress(
    guild_id: int,
    user_id: int,
) -> list[AchievementProgress]:
    catalog = load_catalog()

    with db_session() as connection:
        rows = connection.execute(
            """
            SELECT achievement_key, progress, unlocked_at
            FROM achievement_progress_v5
            WHERE guild_id = ? AND user_id = ?
            """,
            (guild_id, user_id),
        ).fetchall()

    stored = {
        row["achievement_key"]: row
        for row in rows
    }

    results: list[AchievementProgress] = []

    for definition in catalog.values():
        row = stored.get(definition.key)
        current = int(row["progress"]) if row else 0
        unlocked = bool(row and row["unlocked_at"])

        results.append(
            AchievementProgress(
                definition=definition,
                current=current,
                unlocked=unlocked,
            )
        )

    return sorted(
        results,
        key=lambda entry: (
            not entry.unlocked,
            entry.definition.category,
            entry.definition.target,
        ),
    )


def set_showcase(
    guild_id: int,
    user_id: int,
    achievement_key: str,
) -> bool:
    definition = get_definition(achievement_key)

    if definition is None:
        return False

    with db_session() as connection:
        row = connection.execute(
            """
            SELECT unlocked_at
            FROM achievement_progress_v5
            WHERE guild_id = ?
              AND user_id = ?
              AND achievement_key = ?
            """,
            (
                guild_id,
                user_id,
                achievement_key,
            ),
        ).fetchone()

        if row is None or row["unlocked_at"] is None:
            return False

        connection.execute(
            """
            INSERT INTO achievement_showcase_v5 (
                guild_id,
                user_id,
                achievement_key,
                updated_at
            )
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT (guild_id, user_id)
            DO UPDATE SET
                achievement_key = excluded.achievement_key,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                guild_id,
                user_id,
                achievement_key,
            ),
        )

    return True


def get_showcase(
    guild_id: int,
    user_id: int,
):
    with db_session() as connection:
        row = connection.execute(
            """
            SELECT achievement_key
            FROM achievement_showcase_v5
            WHERE guild_id = ? AND user_id = ?
            """,
            (guild_id, user_id),
        ).fetchone()

    if row is None:
        return None

    return get_definition(row["achievement_key"])


def completion_summary(
    guild_id: int,
    user_id: int,
) -> tuple[int, int, int]:
    progress = get_progress(guild_id, user_id)
    total = len(progress)
    completed = sum(1 for entry in progress if entry.unlocked)
    percentage = int((completed / total) * 100) if total else 0

    return completed, total, percentage


def leaderboard(
    guild_id: int,
    limit: int = 10,
) -> list[dict]:
    with db_session() as connection:
        rows = connection.execute(
            """
            SELECT
                user_id,
                COUNT(*) AS completed
            FROM achievement_progress_v5
            WHERE guild_id = ?
              AND unlocked_at IS NOT NULL
            GROUP BY user_id
            ORDER BY completed DESC, user_id ASC
            LIMIT ?
            """,
            (
                guild_id,
                limit,
            ),
        ).fetchall()

    return [
        {
            "user_id": row["user_id"],
            "completed": row["completed"],
        }
        for row in rows
    ]
