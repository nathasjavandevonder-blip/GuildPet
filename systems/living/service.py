from __future__ import annotations

import random

from core.database import db_session
from systems.achievements.service import add_progress
from systems.living.models import (
    CareAction,
    CareResult,
    DragonMood,
    LivingState,
)
from systems.living.personality import add_trait_progress
from systems.relationships.service import (
    record_relationship_action,
)


ACTION_EFFECTS = {
    CareAction.FEED: {
        "hunger": 22,
        "happiness": 2,
        "energy": 1,
        "cleanliness": -2,
        "bond": 2,
        "activity": "eating",
        "metric": "feeds",
    },
    CareAction.PLAY: {
        "hunger": -4,
        "happiness": 16,
        "energy": -8,
        "cleanliness": -3,
        "bond": 3,
        "activity": "playing",
        "metric": "plays",
    },
    CareAction.TRAIN: {
        "hunger": -6,
        "happiness": 4,
        "energy": -12,
        "cleanliness": -4,
        "bond": 2,
        "activity": "training",
        "metric": "trains",
    },
    CareAction.CLEAN: {
        "hunger": 0,
        "happiness": 5,
        "energy": 1,
        "cleanliness": 28,
        "bond": 2,
        "activity": "freshly cleaned",
        "metric": "cleans",
    },
    CareAction.BOND: {
        "hunger": 0,
        "happiness": 10,
        "energy": 2,
        "cleanliness": 0,
        "bond": 8,
        "activity": "spending time with the guild",
        "metric": "bond_actions",
    },
    CareAction.WHISPER: {
        "hunger": 0,
        "happiness": 2,
        "energy": 2,
        "cleanliness": 0,
        "bond": 2,
        "activity": "dreaming peacefully",
        "metric": "bond_actions",
    },
    CareAction.CUDDLE: {
        "hunger": 0,
        "happiness": 5,
        "energy": 3,
        "cleanliness": 0,
        "bond": 4,
        "activity": "sleeping safely",
        "metric": "bond_actions",
    },
    CareAction.LET_SLEEP: {
        "hunger": -1,
        "happiness": 2,
        "energy": 8,
        "cleanliness": 0,
        "bond": 1,
        "activity": "sleeping deeply",
        "metric": None,
    },
    CareAction.WAKE_GENTLY: {
        "hunger": -1,
        "happiness": 3,
        "energy": 1,
        "cleanliness": 0,
        "bond": 3,
        "activity": "waking up",
        "metric": "gentle_wakeups",
    },
}


ACTION_MESSAGES = {
    CareAction.FEED: (
        "🍖 **{username}** fed the dragon. It happily finishes "
        "every bite."
    ),
    CareAction.PLAY: (
        "🎮 **{username}** played with the dragon until its tail "
        "started wagging."
    ),
    CareAction.TRAIN: (
        "🏋️ **{username}** trained with the dragon. Its stance "
        "looks stronger."
    ),
    CareAction.CLEAN: (
        "🛁 **{username}** cleaned the dragon and its resting area."
    ),
    CareAction.BOND: (
        "❤️ **{username}** spent quiet time bonding with the dragon."
    ),
    CareAction.WHISPER: (
        "🤫 **{username}** whispered softly. The dragon smiles "
        "in its sleep."
    ),
    CareAction.CUDDLE: (
        "💖 **{username}** cuddled beside the sleeping dragon."
    ),
    CareAction.LET_SLEEP: (
        "🌙 **{username}** kept the lair quiet and let the dragon rest."
    ),
    CareAction.WAKE_GENTLY: (
        "☕ **{username}** gently woke the dragon."
    ),
}


def clamp(value: int) -> int:
    return max(0, min(100, value))


def calculate_mood(
    *,
    hunger: int,
    happiness: int,
    energy: int,
    cleanliness: int,
    bond: int,
) -> DragonMood:
    if hunger <= 20:
        return DragonMood.HUNGRY

    if energy <= 20:
        return DragonMood.SLEEPY

    if cleanliness <= 20:
        return DragonMood.DIRTY

    if happiness <= 25:
        return DragonMood.LONELY

    if happiness >= 85 and energy >= 45:
        return DragonMood.EXCITED

    if happiness >= 70:
        return DragonMood.HAPPY

    if bond <= 5 and happiness < 50:
        return DragonMood.GRUMPY

    return DragonMood.CONTENT


def ensure_living_state(guild_id: int) -> LivingState:
    with db_session() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO dragon_living_v5 (
                guild_id,
                updated_at
            )
            VALUES (?, CURRENT_TIMESTAMP)
            """,
            (guild_id,),
        )

    return get_living_state(guild_id)


def get_living_state(guild_id: int) -> LivingState:
    with db_session() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM dragon_living_v5
            WHERE guild_id = ?
            """,
            (guild_id,),
        ).fetchone()

    if row is None:
        return ensure_living_state(guild_id)

    return LivingState(
        guild_id=int(row["guild_id"]),
        hunger=int(row["hunger"]),
        happiness=int(row["happiness"]),
        energy=int(row["energy"]),
        cleanliness=int(row["cleanliness"]),
        bond=int(row["bond"]),
        mood=DragonMood(row["mood"]),
        current_activity=str(row["current_activity"]),
    )


def add_memory(
    guild_id: int,
    *,
    user_id: int | None,
    username: str | None,
    memory_type: str,
    memory_text: str,
    importance: int = 1,
) -> None:
    with db_session() as connection:
        connection.execute(
            """
            INSERT INTO dragon_memories_living_v5 (
                guild_id,
                user_id,
                username,
                memory_type,
                memory_text,
                importance
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                guild_id,
                user_id,
                username,
                memory_type,
                memory_text,
                importance,
            ),
        )


def perform_care_action(
    guild_id: int,
    *,
    user_id: int,
    username: str,
    action: CareAction,
) -> CareResult:
    current = ensure_living_state(guild_id)
    effect = ACTION_EFFECTS[action]

    hunger = clamp(current.hunger + effect["hunger"])
    happiness = clamp(current.happiness + effect["happiness"])
    energy = clamp(current.energy + effect["energy"])
    cleanliness = clamp(
        current.cleanliness + effect["cleanliness"]
    )
    bond = clamp(current.bond + effect["bond"])

    mood = calculate_mood(
        hunger=hunger,
        happiness=happiness,
        energy=energy,
        cleanliness=cleanliness,
        bond=bond,
    )

    with db_session() as connection:
        connection.execute(
            """
            UPDATE dragon_living_v5
            SET hunger = ?,
                happiness = ?,
                energy = ?,
                cleanliness = ?,
                bond = ?,
                mood = ?,
                current_activity = ?,
                last_care_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE guild_id = ?
            """,
            (
                hunger,
                happiness,
                energy,
                cleanliness,
                bond,
                mood.value,
                effect["activity"],
                guild_id,
            ),
        )

    add_trait_progress(guild_id, action.value)

    relationship_bond = record_relationship_action(
        guild_id,
        user_id,
        username,
        action.value,
    )

    unlocked: list[str] = []

    metric = effect.get("metric")

    if metric:
        unlocked.extend(
            add_progress(
                guild_id,
                user_id,
                metric,
                1,
            )
        )

    if action in {
        CareAction.FEED,
        CareAction.PLAY,
        CareAction.TRAIN,
        CareAction.CLEAN,
        CareAction.BOND,
    }:
        unlocked.extend(
            add_progress(
                guild_id,
                user_id,
                "care_actions",
                1,
            )
        )

    if random.random() < 0.12:
        add_memory(
            guild_id,
            user_id=user_id,
            username=username,
            memory_type="care",
            memory_text=(
                f"{username} used {action.value} and spent time "
                "with the dragon."
            ),
        )

    return CareResult(
        action=action,
        message=ACTION_MESSAGES[action].format(
            username=username,
        ),
        living_state=get_living_state(guild_id),
        unlocked_achievements=tuple(dict.fromkeys(unlocked)),
        relationship_bond=relationship_bond,
    )


def apply_passive_decay(
    guild_id: int,
    *,
    steps: int = 1,
) -> LivingState:
    current = ensure_living_state(guild_id)

    hunger = clamp(current.hunger - (2 * steps))
    happiness = clamp(current.happiness - steps)
    energy = clamp(current.energy - steps)
    cleanliness = clamp(current.cleanliness - steps)

    mood = calculate_mood(
        hunger=hunger,
        happiness=happiness,
        energy=energy,
        cleanliness=cleanliness,
        bond=current.bond,
    )

    with db_session() as connection:
        connection.execute(
            """
            UPDATE dragon_living_v5
            SET hunger = ?,
                happiness = ?,
                energy = ?,
                cleanliness = ?,
                mood = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE guild_id = ?
            """,
            (
                hunger,
                happiness,
                energy,
                cleanliness,
                mood.value,
                guild_id,
            ),
        )

    return get_living_state(guild_id)



def apply_combat_aftermath(guild_id: int) -> LivingState:
    """Apply fatigue and excitement immediately after combat."""
    current = ensure_living_state(guild_id)

    hunger = clamp(current.hunger - 4)
    happiness = clamp(current.happiness + 4)
    energy = clamp(current.energy - 12)
    cleanliness = clamp(current.cleanliness - 3)

    mood = calculate_mood(
        hunger=hunger,
        happiness=happiness,
        energy=energy,
        cleanliness=cleanliness,
        bond=current.bond,
    )

    with db_session() as connection:
        connection.execute(
            """
            UPDATE dragon_living_v5
            SET hunger = ?,
                happiness = ?,
                energy = ?,
                cleanliness = ?,
                mood = ?,
                current_activity = 'catching its breath',
                updated_at = CURRENT_TIMESTAMP
            WHERE guild_id = ?
            """,
            (
                hunger,
                happiness,
                energy,
                cleanliness,
                mood.value,
                guild_id,
            ),
        )

    return get_living_state(guild_id)


def finish_combat_recovery(guild_id: int) -> LivingState:
    """Return the dragon to its normal post-combat activity."""
    current = ensure_living_state(guild_id)

    energy = clamp(current.energy + 5)

    mood = calculate_mood(
        hunger=current.hunger,
        happiness=current.happiness,
        energy=energy,
        cleanliness=current.cleanliness,
        bond=current.bond,
    )

    with db_session() as connection:
        connection.execute(
            """
            UPDATE dragon_living_v5
            SET energy = ?,
                mood = ?,
                current_activity = 'watching the guild',
                updated_at = CURRENT_TIMESTAMP
            WHERE guild_id = ?
            """,
            (
                energy,
                mood.value,
                guild_id,
            ),
        )

    return get_living_state(guild_id)
