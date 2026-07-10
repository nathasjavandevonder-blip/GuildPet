from __future__ import annotations

from core.database import db_session

TRAITS = (
    "friendly",
    "brave",
    "curious",
    "playful",
    "gentle",
    "protective",
    "lazy",
    "mischievous",
)

ACTION_TRAITS = {
    "feed": ("friendly", 2),
    "play": ("playful", 3),
    "train": ("brave", 3),
    "clean": ("gentle", 2),
    "bond": ("friendly", 3),
    "whisper": ("gentle", 2),
    "cuddle": ("friendly", 3),
    "let_sleep": ("lazy", 1),
    "wake_gently": ("gentle", 3),
}


def ensure_personality(guild_id: int) -> None:
    with db_session() as connection:
        for trait in TRAITS:
            connection.execute(
                """
                INSERT OR IGNORE INTO dragon_personality_v5 (
                    guild_id,
                    trait,
                    score,
                    updated_at
                )
                VALUES (?, ?, 0, CURRENT_TIMESTAMP)
                """,
                (guild_id, trait),
            )


def add_trait_progress(
    guild_id: int,
    action: str,
) -> None:
    ensure_personality(guild_id)

    trait_data = ACTION_TRAITS.get(action)

    if trait_data is None:
        trait_data = ("curious", 1)

    trait, amount = trait_data

    with db_session() as connection:
        connection.execute(
            """
            UPDATE dragon_personality_v5
            SET score = score + ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE guild_id = ? AND trait = ?
            """,
            (amount, guild_id, trait),
        )


def get_personality(
    guild_id: int,
) -> list[tuple[str, int]]:
    ensure_personality(guild_id)

    with db_session() as connection:
        rows = connection.execute(
            """
            SELECT trait, score
            FROM dragon_personality_v5
            WHERE guild_id = ?
            ORDER BY score DESC, trait ASC
            """,
            (guild_id,),
        ).fetchall()

    return [
        (row["trait"], int(row["score"]))
        for row in rows
    ]


def dominant_personality(guild_id: int) -> str:
    scores = get_personality(guild_id)

    if not scores or scores[0][1] <= 0:
        return "curious"

    return scores[0][0]
