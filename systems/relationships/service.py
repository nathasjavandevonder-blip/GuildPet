from __future__ import annotations

from core.database import db_session


ACTION_VALUES = {
    "feed": {
        "bond": 2,
        "trust": 2,
        "care_actions": 1,
    },
    "play": {
        "bond": 3,
        "trust": 1,
        "play_actions": 1,
    },
    "train": {
        "bond": 2,
        "trust": 2,
        "training_actions": 1,
    },
    "clean": {
        "bond": 2,
        "trust": 3,
        "care_actions": 1,
    },
    "bond": {
        "bond": 5,
        "trust": 3,
    },
    "whisper": {
        "bond": 2,
        "trust": 2,
    },
    "cuddle": {
        "bond": 4,
        "trust": 3,
    },
    "let_sleep": {
        "bond": 1,
        "trust": 2,
    },
    "wake_gently": {
        "bond": 3,
        "trust": 3,
        "gentle_wakeups": 1,
    },
}


def record_relationship_action(
    guild_id: int,
    user_id: int,
    username: str,
    action: str,
) -> int:
    values = ACTION_VALUES.get(
        action,
        {"bond": 1, "trust": 0},
    )

    bond = int(values.get("bond", 0))
    trust = int(values.get("trust", 0))
    care_actions = int(values.get("care_actions", 0))
    play_actions = int(values.get("play_actions", 0))
    training_actions = int(values.get("training_actions", 0))
    gentle_wakeups = int(values.get("gentle_wakeups", 0))

    with db_session() as connection:
        connection.execute(
            """
            INSERT INTO dragon_relationships_v5 (
                guild_id,
                user_id,
                username,
                bond,
                trust,
                care_actions,
                play_actions,
                training_actions,
                gentle_wakeups,
                last_interaction,
                updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                CURRENT_TIMESTAMP
            )
            ON CONFLICT (guild_id, user_id)
            DO UPDATE SET
                username = excluded.username,
                bond = bond + excluded.bond,
                trust = trust + excluded.trust,
                care_actions = care_actions + excluded.care_actions,
                play_actions = play_actions + excluded.play_actions,
                training_actions =
                    training_actions + excluded.training_actions,
                gentle_wakeups =
                    gentle_wakeups + excluded.gentle_wakeups,
                last_interaction = excluded.last_interaction,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                guild_id,
                user_id,
                username,
                bond,
                trust,
                care_actions,
                play_actions,
                training_actions,
                gentle_wakeups,
                action,
            ),
        )

        row = connection.execute(
            """
            SELECT bond
            FROM dragon_relationships_v5
            WHERE guild_id = ? AND user_id = ?
            """,
            (guild_id, user_id),
        ).fetchone()

    return int(row["bond"]) if row else 0


def get_relationship(
    guild_id: int,
    user_id: int,
):
    with db_session() as connection:
        return connection.execute(
            """
            SELECT *
            FROM dragon_relationships_v5
            WHERE guild_id = ? AND user_id = ?
            """,
            (guild_id, user_id),
        ).fetchone()


def relationship_title(
    guild_id: int,
    user_id: int,
) -> str:
    relationship = get_relationship(guild_id, user_id)

    if relationship is None:
        return "New Keeper"

    bond = int(relationship["bond"])

    if bond >= 500:
        return "Dragon Whisperer"

    if bond >= 250:
        return "Favorite Keeper"

    if bond >= 100:
        return "Trusted Friend"

    if bond >= 40:
        return "Dragon Friend"

    if bond >= 10:
        return "Familiar Keeper"

    return "New Keeper"


def top_relationships(
    guild_id: int,
    limit: int = 10,
):
    with db_session() as connection:
        return connection.execute(
            """
            SELECT
                user_id,
                username,
                bond,
                trust,
                care_actions,
                play_actions,
                training_actions
            FROM dragon_relationships_v5
            WHERE guild_id = ?
            ORDER BY bond DESC, trust DESC
            LIMIT ?
            """,
            (guild_id, limit),
        ).fetchall()
