from __future__ import annotations

from dataclasses import dataclass

from core.database import db_session
from systems.living.service import get_living_state
from systems.onboarding.service import resolve_lifecycle
from systems.state.models import DragonState
from systems.state.service import resolve_expired_state
from systems.world.catalog import get_location, get_weather
from systems.world.service import ensure_world_state


STATE_LABELS: dict[DragonState, str] = {
    DragonState.IDLE: "Relaxing",
    DragonState.SLEEPING: "Sleeping",
    DragonState.ADVENTURE: "On Adventure",
    DragonState.COMBAT: "In Combat",
    DragonState.TRAVELLING: "Travelling",
    DragonState.RECOVERING: "Recovering",
    DragonState.CELEBRATING: "Celebrating",
}

STAGE_LABELS = {
    "unconfigured": "Awaiting Setup",
    "egg_vote": "Ancient Egg Vote",
    "incubating": "Ancient Egg",
    "hatchling": "Hatchling",
    "young": "Young Dragon",
    "adult": "Adult Dragon",
    "ancient": "Ancient Dragon",
    "elder": "Elder Dragon",
    "legacy": "Guardian Legacy",
}


@dataclass(frozen=True, slots=True)
class DragonStatus:
    guild_id: int
    name: str
    title: str
    stage: str
    stage_label: str
    level: int
    growth: int
    xp: int
    hunger: int
    happiness: int
    energy: int
    cleanliness: int
    bond: int
    mood: str
    activity: str
    state: DragonState
    state_label: str
    location_name: str
    location_emoji: str
    weather_name: str
    weather_emoji: str
    time_period: str
    season: str
    personality: str
    selected_egg: str | None
    recent_activity: tuple[str, ...]

    @property
    def thought(self) -> str:
        if self.stage == "egg_vote":
            return "Which ancient spirit will our guild choose?"
        if self.stage == "incubating":
            return "I can hear you through the shell... please stay close."
        if self.stage == "hatchling":
            return "The world feels enormous, but this guild feels safe."
        if self.mood == "hungry":
            return "My tummy is rumbling. Did someone bring a snack?"
        if self.mood == "sleepy":
            return "I think a warm, quiet nap would be wonderful."
        if self.mood == "lonely":
            return "Could someone stay with me for a little while?"
        if self.mood == "dirty":
            return "I may have explored somewhere a little too muddy..."
        if self.mood in {"happy", "excited"}:
            return "I cannot wait to see what our guild does today!"
        return "I wonder what lies beyond our home..."


def _ensure_profile(guild_id: int) -> None:
    with db_session() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO dragon_profile_v5 (
                guild_id, dragon_name, title, level, xp, growth, personality
            ) VALUES (?, 'Guild Dragon', 'Guardian in Training', 1, 0, 0, 'Curious')
            """,
            (guild_id,),
        )


def _load_recent_activity(guild_id: int, limit: int = 3) -> tuple[str, ...]:
    with db_session() as connection:
        rows = connection.execute(
            """
            SELECT activity_text
            FROM dashboard_activity_v5
            WHERE guild_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (guild_id, limit),
        ).fetchall()

        if not rows:
            rows = connection.execute(
                """
                SELECT memory_text AS activity_text
                FROM dragon_memories_living_v5
                WHERE guild_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (guild_id, limit),
            ).fetchall()

    return tuple(str(row["activity_text"]) for row in rows)


def load_dragon_status(guild_id: int) -> DragonStatus:
    _ensure_profile(guild_id)

    lifecycle = resolve_lifecycle(guild_id)
    living = get_living_state(guild_id)
    state = resolve_expired_state(guild_id)
    world = ensure_world_state(guild_id)
    location = get_location(world.location_key)
    weather = get_weather(world.weather_key)

    with db_session() as connection:
        profile = connection.execute(
            "SELECT * FROM dragon_profile_v5 WHERE guild_id = ?",
            (guild_id,),
        ).fetchone()

    return DragonStatus(
        guild_id=guild_id,
        name=str(profile["dragon_name"]),
        title=str(profile["title"]),
        stage=lifecycle.stage,
        stage_label=STAGE_LABELS.get(lifecycle.stage, lifecycle.stage.title()),
        level=max(1, int(profile["level"])),
        growth=max(0, min(100, int(profile["growth"]))),
        xp=max(0, int(profile["xp"])),
        hunger=living.hunger,
        happiness=living.happiness,
        energy=living.energy,
        cleanliness=living.cleanliness,
        bond=living.bond,
        mood=living.mood.value,
        activity=living.current_activity,
        state=state.state,
        state_label=STATE_LABELS[state.state],
        location_name=location.name,
        location_emoji=location.emoji,
        weather_name=weather.name,
        weather_emoji=weather.emoji,
        time_period=world.time_period,
        season=world.season_key,
        personality=str(profile["personality"]),
        selected_egg=lifecycle.selected_egg,
        recent_activity=_load_recent_activity(guild_id),
    )
