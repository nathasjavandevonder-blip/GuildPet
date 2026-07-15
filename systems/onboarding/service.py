from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import random

from core.database import db_session

EGGS = {
    "crimson": ("Crimson Egg", "Warm and resolute", "Courage, determination and strength"),
    "azure": ("Azure Egg", "Cool and tranquil", "Wisdom, patience and magic"),
    "emerald": ("Emerald Egg", "Alive with gentle energy", "Compassion, healing and growth"),
    "ivory": ("Ivory Egg", "Calm and reassuring", "Loyalty, balance and protection"),
    "shadow": ("Shadow Egg", "Mysterious and watchful", "Curiosity, cunning and adaptability"),
    "golden": ("Golden Egg", "Bright and inspiring", "Leadership, charisma and luck"),
}

EGG_TRAIT_BONUSES = {
    "crimson": {"courage": 12, "determination": 12, "strength": 10},
    "azure": {"wisdom": 12, "patience": 12, "magic": 10},
    "emerald": {"compassion": 12, "healing": 12, "growth": 10},
    "ivory": {"loyalty": 12, "balance": 12, "protection": 10},
    "shadow": {"curiosity": 12, "cunning": 12, "adaptability": 10},
    "golden": {"leadership": 12, "charisma": 12, "luck": 10},
}

STAGE_ORDER = {
    "unconfigured": 0,
    "egg_vote": 1,
    "incubating": 2,
    "hatchling": 3,
    "young": 4,
    "adult": 5,
    "ancient": 6,
    "elder": 7,
    "legacy": 8,
}


@dataclass(slots=True)
class Lifecycle:
    guild_id: int
    stage: str
    selected_egg: str | None
    vote_ends_at: datetime | None
    hatch_at: datetime | None
    egg_care_required: int = 5


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed


def utc_now() -> datetime:
    return datetime.now(UTC)


def get_setup(guild_id: int):
    with db_session() as con:
        return con.execute(
            "SELECT * FROM guild_setup_v55 WHERE guild_id=?",
            (guild_id,),
        ).fetchone()


def save_setup(guild_id: int, **values) -> None:
    allowed = {
        "dragon_channel_id", "welcome_channel_id", "log_channel_id", "ai_activity",
        "ai_max_per_hour", "welcome_enabled", "mention_replies", "spontaneous_chat",
        "vote_duration_hours", "incubation_days", "setup_complete",
    }
    clean = {key: value for key, value in values.items() if key in allowed}
    with db_session() as con:
        con.execute(
            "INSERT OR IGNORE INTO guild_setup_v55 (guild_id) VALUES (?)",
            (guild_id,),
        )
        for key, value in clean.items():
            con.execute(
                f"UPDATE guild_setup_v55 SET {key}=?, updated_at=CURRENT_TIMESTAMP WHERE guild_id=?",
                (value, guild_id),
            )
        con.execute(
            "INSERT OR IGNORE INTO dragon_lifecycle_v55 (guild_id) VALUES (?)",
            (guild_id,),
        )


def set_ai_channels(guild_id: int, channel_ids: list[int]) -> None:
    with db_session() as con:
        con.execute("DELETE FROM guild_ai_channels_v55 WHERE guild_id=?", (guild_id,))
        con.executemany(
            "INSERT INTO guild_ai_channels_v55 (guild_id, channel_id) VALUES (?, ?)",
            [(guild_id, channel_id) for channel_id in dict.fromkeys(channel_ids)],
        )


def get_ai_channels(guild_id: int) -> list[int]:
    with db_session() as con:
        rows = con.execute(
            "SELECT channel_id FROM guild_ai_channels_v55 WHERE guild_id=?",
            (guild_id,),
        ).fetchall()
    return [int(row["channel_id"]) for row in rows]


def get_lifecycle(guild_id: int) -> Lifecycle:
    with db_session() as con:
        con.execute(
            "INSERT OR IGNORE INTO dragon_lifecycle_v55 (guild_id) VALUES (?)",
            (guild_id,),
        )
        row = con.execute(
            "SELECT * FROM dragon_lifecycle_v55 WHERE guild_id=?",
            (guild_id,),
        ).fetchone()
    keys = set(row.keys())
    care_required = int(row["egg_care_required"]) if "egg_care_required" in keys else 5
    return Lifecycle(
        guild_id,
        row["lifecycle_stage"],
        row["selected_egg"],
        _parse(row["vote_ends_at"]),
        _parse(row["hatch_at"]),
        care_required,
    )


def start_egg_vote(guild_id: int) -> Lifecycle:
    setup = get_setup(guild_id)
    if setup is None or not setup["setup_complete"]:
        raise ValueError("Finish the GuildPet setup first.")
    lifecycle = get_lifecycle(guild_id)
    if lifecycle.stage != "unconfigured":
        raise ValueError("This server already started its dragon journey.")
    now = utc_now()
    ends = now + timedelta(hours=int(setup["vote_duration_hours"]))
    with db_session() as con:
        con.execute("DELETE FROM egg_votes_v55 WHERE guild_id=?", (guild_id,))
        con.execute(
            """UPDATE dragon_lifecycle_v55
               SET lifecycle_stage='egg_vote', vote_started_at=?, vote_ends_at=?,
                   selected_egg=NULL, updated_at=CURRENT_TIMESTAMP
               WHERE guild_id=?""",
            (now.isoformat(), ends.isoformat(), guild_id),
        )
        con.execute(
            "INSERT INTO guild_chronicle_v55 (guild_id, event_key, event_text) VALUES (?, 'egg_vote_started', ?)",
            (guild_id, "The guild began its first ancient egg vote."),
        )
    return get_lifecycle(guild_id)


def cast_vote(guild_id: int, user_id: int, egg_key: str) -> None:
    if egg_key not in EGGS:
        raise ValueError("Unknown egg.")
    lifecycle = resolve_lifecycle(guild_id)
    if lifecycle.stage != "egg_vote":
        raise ValueError("The egg vote is not active.")
    with db_session() as con:
        con.execute(
            """INSERT INTO egg_votes_v55 (guild_id, user_id, egg_key) VALUES (?, ?, ?)
               ON CONFLICT(guild_id, user_id) DO UPDATE SET
                   egg_key=excluded.egg_key,
                   voted_at=CURRENT_TIMESTAMP""",
            (guild_id, user_id, egg_key),
        )


def vote_counts(guild_id: int) -> dict[str, int]:
    counts = {key: 0 for key in EGGS}
    with db_session() as con:
        rows = con.execute(
            "SELECT egg_key, COUNT(*) AS total FROM egg_votes_v55 WHERE guild_id=? GROUP BY egg_key",
            (guild_id,),
        ).fetchall()
    for row in rows:
        if row["egg_key"] in counts:
            counts[row["egg_key"]] = int(row["total"])
    return counts


def total_votes(guild_id: int) -> int:
    return sum(vote_counts(guild_id).values())


def _apply_egg_traits(connection, guild_id: int, egg_key: str) -> None:
    connection.execute(
        "INSERT OR IGNORE INTO dragon_traits_v55 (guild_id) VALUES (?)",
        (guild_id,),
    )
    bonuses = EGG_TRAIT_BONUSES[egg_key]
    assignments = ", ".join(f"{trait}={trait}+?" for trait in bonuses)
    values = [*bonuses.values(), egg_key, guild_id]
    connection.execute(
        f"""UPDATE dragon_traits_v55
            SET {assignments}, source_egg=?, updated_at=CURRENT_TIMESTAMP
            WHERE guild_id=?""",
        values,
    )


def finalize_vote(guild_id: int, *, force: bool = False) -> str:
    lifecycle = get_lifecycle(guild_id)
    if lifecycle.stage != "egg_vote":
        if lifecycle.selected_egg:
            return lifecycle.selected_egg
        raise ValueError("There is no active egg vote.")
    if not force and lifecycle.vote_ends_at and utc_now() < lifecycle.vote_ends_at:
        raise ValueError("The egg vote has not ended yet.")

    counts = vote_counts(guild_id)
    highest = max(counts.values())
    winners = [key for key, value in counts.items() if value == highest]
    chosen = random.choice(winners)
    setup = get_setup(guild_id)
    now = utc_now()
    hatch_at = now + timedelta(days=int(setup["incubation_days"] if setup else 7))
    egg_name = EGGS[chosen][0]

    with db_session() as con:
        con.execute(
            """UPDATE dragon_lifecycle_v55
               SET lifecycle_stage='incubating', selected_egg=?, incubation_started_at=?,
                   hatch_at=?, updated_at=CURRENT_TIMESTAMP
               WHERE guild_id=?""",
            (chosen, now.isoformat(), hatch_at.isoformat(), guild_id),
        )
        _apply_egg_traits(con, guild_id, chosen)
        con.execute(
            "INSERT INTO guild_chronicle_v55 (guild_id, event_key, event_text) VALUES (?, 'egg_chosen', ?)",
            (guild_id, f"The guild chose the {egg_name}."),
        )
        con.execute(
            "INSERT INTO dragon_diary_v55 (guild_id, entry_type, entry_text) VALUES (?, 'egg', ?)",
            (guild_id, "Many voices gathered around me today. I think they chose me."),
        )
    return chosen


def egg_care_count(guild_id: int) -> int:
    with db_session() as con:
        row = con.execute(
            "SELECT COUNT(*) AS total FROM egg_care_v55 WHERE guild_id=?",
            (guild_id,),
        ).fetchone()
    return int(row["total"])


def egg_care_breakdown(guild_id: int) -> dict[str, int]:
    result = {key: 0 for key in ("cuddle", "warm", "sing", "story", "guard")}
    with db_session() as con:
        rows = con.execute(
            "SELECT action_key, COUNT(*) AS total FROM egg_care_v55 WHERE guild_id=? GROUP BY action_key",
            (guild_id,),
        ).fetchall()
    for row in rows:
        result[row["action_key"]] = int(row["total"])
    return result


def resolve_lifecycle(guild_id: int) -> Lifecycle:
    lifecycle = get_lifecycle(guild_id)
    now = utc_now()
    if lifecycle.stage == "egg_vote" and lifecycle.vote_ends_at and now >= lifecycle.vote_ends_at:
        finalize_vote(guild_id)
        lifecycle = get_lifecycle(guild_id)

    if lifecycle.stage == "incubating" and lifecycle.hatch_at and now >= lifecycle.hatch_at:
        if egg_care_count(guild_id) >= lifecycle.egg_care_required:
            with db_session() as con:
                con.execute(
                    """UPDATE dragon_lifecycle_v55
                       SET lifecycle_stage='hatchling', hatched_at=?, updated_at=CURRENT_TIMESTAMP
                       WHERE guild_id=?""",
                    (now.isoformat(), guild_id),
                )
                con.execute(
                    "INSERT INTO guild_chronicle_v55 (guild_id, event_key, event_text) VALUES (?, 'first_hatch', ?)",
                    (guild_id, "The guild's first dragon hatched."),
                )
                con.execute(
                    "INSERT INTO dragon_diary_v55 (guild_id, entry_type, entry_text) VALUES (?, 'hatch', ?)",
                    (guild_id, "The shell opened. The voices outside were my family."),
                )
            lifecycle = get_lifecycle(guild_id)
    return lifecycle


def feature_unlocked(guild_id: int, feature_key: str) -> bool:
    lifecycle = resolve_lifecycle(guild_id)
    with db_session() as con:
        row = con.execute(
            "SELECT required_stage FROM feature_unlocks_v55 WHERE feature_key=?",
            (feature_key,),
        ).fetchone()
    if row is None:
        return True
    return STAGE_ORDER.get(lifecycle.stage, 0) >= STAGE_ORDER.get(row["required_stage"], 999)


def locked_reason(guild_id: int, feature_key: str) -> str | None:
    if feature_unlocked(guild_id, feature_key):
        return None
    with db_session() as con:
        row = con.execute(
            "SELECT required_stage, description FROM feature_unlocks_v55 WHERE feature_key=?",
            (feature_key,),
        ).fetchone()
    if row is None:
        return None
    required = row["required_stage"].replace("_", " ").title()
    return f"**{row['description']}** unlocks when the dragon reaches the **{required}** stage."


def register_egg_care(guild_id: int, user_id: int, action_key: str) -> bool:
    if action_key not in {"cuddle", "warm", "sing", "story", "guard"}:
        raise ValueError("Unknown egg-care action.")
    lifecycle = resolve_lifecycle(guild_id)
    if lifecycle.stage != "incubating":
        raise ValueError("There is no egg to care for right now.")
    today = utc_now().date().isoformat()
    with db_session() as con:
        existing = con.execute(
            "SELECT 1 FROM egg_care_v55 WHERE guild_id=? AND user_id=? AND care_date=?",
            (guild_id, user_id, today),
        ).fetchone()
        if existing:
            return False
        con.execute(
            "INSERT INTO egg_care_v55 (guild_id, user_id, care_date, action_key) VALUES (?, ?, ?, ?)",
            (guild_id, user_id, today, action_key),
        )
        messages = {
            "cuddle": "Someone held me close today. I felt safe.",
            "warm": "The nest was warm. I slept peacefully.",
            "sing": "A soft song reached me through the shell.",
            "story": "I heard a story about the world waiting outside.",
            "guard": "Someone stayed nearby to protect me.",
        }
        con.execute(
            "INSERT INTO dragon_diary_v55 (guild_id, entry_type, entry_text) VALUES (?, 'egg_care', ?)",
            (guild_id, messages[action_key]),
        )
    resolve_lifecycle(guild_id)
    return True


def register_hatchling_care(guild_id: int, user_id: int, action_key: str) -> bool:
    if action_key not in {"feed", "play", "rest", "bond", "story"}:
        raise ValueError("Unknown hatchling-care action.")
    lifecycle = resolve_lifecycle(guild_id)
    if lifecycle.stage != "hatchling":
        raise ValueError("The dragon is not a hatchling right now.")
    today = utc_now().date().isoformat()
    with db_session() as con:
        existing = con.execute(
            "SELECT 1 FROM hatchling_care_v55 WHERE guild_id=? AND user_id=? AND care_date=?",
            (guild_id, user_id, today),
        ).fetchone()
        if existing:
            return False
        con.execute(
            "INSERT INTO hatchling_care_v55 (guild_id, user_id, care_date, action_key) VALUES (?, ?, ?, ?)",
            (guild_id, user_id, today, action_key),
        )
    return True


def recent_diary(guild_id: int, limit: int = 5):
    with db_session() as con:
        return con.execute(
            "SELECT entry_text, created_at FROM dragon_diary_v55 WHERE guild_id=? ORDER BY entry_id DESC LIMIT ?",
            (guild_id, limit),
        ).fetchall()
# Developer and management helpers. These are deliberately kept in the
# onboarding service so every UI and command uses the same lifecycle rules.
VALID_STAGES = tuple(STAGE_ORDER)


def force_select_egg(guild_id: int, egg_key: str, *, incubation_days: int | None = None) -> Lifecycle:
    if egg_key not in EGGS:
        raise ValueError("Unknown egg.")
    setup = get_setup(guild_id)
    days = incubation_days if incubation_days is not None else int(setup["incubation_days"] if setup else 7)
    now = utc_now()
    hatch_at = now + timedelta(days=max(0, days))
    with db_session() as con:
        con.execute("INSERT OR IGNORE INTO dragon_lifecycle_v55 (guild_id) VALUES (?)", (guild_id,))
        con.execute(
            """UPDATE dragon_lifecycle_v55
               SET lifecycle_stage='incubating', selected_egg=?, vote_ends_at=?,
                   incubation_started_at=?, hatch_at=?, updated_at=CURRENT_TIMESTAMP
               WHERE guild_id=?""",
            (egg_key, now.isoformat(), now.isoformat(), hatch_at.isoformat(), guild_id),
        )
    return get_lifecycle(guild_id)


def force_stage(guild_id: int, stage: str) -> Lifecycle:
    if stage not in STAGE_ORDER or stage == "unconfigured":
        raise ValueError("Unsupported lifecycle stage.")
    now = utc_now().isoformat()
    with db_session() as con:
        con.execute("INSERT OR IGNORE INTO dragon_lifecycle_v55 (guild_id) VALUES (?)", (guild_id,))
        fields = ["lifecycle_stage=?", "updated_at=CURRENT_TIMESTAMP"]
        values: list[object] = [stage]
        if stage == "egg_vote":
            setup = get_setup(guild_id)
            hours = int(setup["vote_duration_hours"] if setup else 48)
            fields.extend(["vote_started_at=?", "vote_ends_at=?", "selected_egg=NULL"])
            values.extend([now, (utc_now() + timedelta(hours=hours)).isoformat()])
            con.execute("DELETE FROM egg_votes_v55 WHERE guild_id=?", (guild_id,))
        elif stage == "incubating":
            selected = get_lifecycle(guild_id).selected_egg or "crimson"
            setup = get_setup(guild_id)
            days = int(setup["incubation_days"] if setup else 7)
            fields.extend(["selected_egg=?", "incubation_started_at=?", "hatch_at=?"])
            values.extend([selected, now, (utc_now() + timedelta(days=days)).isoformat()])
        elif STAGE_ORDER[stage] >= STAGE_ORDER["hatchling"]:
            fields.append("hatched_at=COALESCE(hatched_at, ?)")
            values.append(now)
        values.append(guild_id)
        con.execute(f"UPDATE dragon_lifecycle_v55 SET {', '.join(fields)} WHERE guild_id=?", values)
    return get_lifecycle(guild_id)


def advance_lifecycle_time(guild_id: int, *, hours: int) -> Lifecycle:
    lifecycle = get_lifecycle(guild_id)
    delta = timedelta(hours=hours)
    with db_session() as con:
        if lifecycle.stage == "egg_vote" and lifecycle.vote_ends_at:
            con.execute(
                "UPDATE dragon_lifecycle_v55 SET vote_ends_at=?, updated_at=CURRENT_TIMESTAMP WHERE guild_id=?",
                ((lifecycle.vote_ends_at - delta).isoformat(), guild_id),
            )
        elif lifecycle.stage == "incubating" and lifecycle.hatch_at:
            con.execute(
                "UPDATE dragon_lifecycle_v55 SET hatch_at=?, updated_at=CURRENT_TIMESTAMP WHERE guild_id=?",
                ((lifecycle.hatch_at - delta).isoformat(), guild_id),
            )
    return resolve_lifecycle(guild_id)


def reset_guildpet_journey(guild_id: int) -> None:
    """Reset only the v5.5 onboarding journey for a test guild."""
    with db_session() as con:
        con.execute("DELETE FROM egg_votes_v55 WHERE guild_id=?", (guild_id,))
        con.execute("DELETE FROM egg_care_v55 WHERE guild_id=?", (guild_id,))
        con.execute(
            """UPDATE dragon_lifecycle_v55 SET lifecycle_stage='unconfigured', selected_egg=NULL,
               vote_started_at=NULL, vote_ends_at=NULL, incubation_started_at=NULL,
               hatch_at=NULL, hatched_at=NULL, updated_at=CURRENT_TIMESTAMP WHERE guild_id=?""",
            (guild_id,),
        )
