import random
from datetime import datetime, timezone, timedelta
import discord

from database import db_session, execute_with_retry, get_dragon, add_memory_tx
from progression import has_research, add_guild_level_xp
from utils import get_stage

ADVENTURES = {
    "forest": {
        "name": "Ancient Forest",
        "emoji": "🌲",
        "minutes": 10,
        "min_xp": 0,
        "reward_tokens": (35, 90),
        "reward_xp": (15, 45),
        "description": "A safe forest route with berries, butterflies and small treasures.",
    },
    "lake": {
        "name": "Crystal Lake",
        "emoji": "🌊",
        "minutes": 20,
        "min_xp": 250,
        "reward_tokens": (70, 150),
        "reward_xp": (30, 80),
        "description": "A calm lake where crystals sometimes wash onto the shore.",
    },
    "ruins": {
        "name": "Ancient Ruins",
        "emoji": "🏛️",
        "minutes": 30,
        "min_xp": 750,
        "reward_tokens": (110, 240),
        "reward_xp": (60, 130),
        "description": "Old ruins with hidden rooms, dusty relics and risky discoveries.",
    },
    "mountains": {
        "name": "Storm Mountains",
        "emoji": "⛰️",
        "minutes": 45,
        "min_xp": 1500,
        "reward_tokens": (180, 360),
        "reward_xp": (90, 210),
        "description": "A dangerous mountain path with strong winds and rare minerals.",
    },
    "volcano": {
        "name": "Fire Volcano",
        "emoji": "🌋",
        "minutes": 60,
        "min_xp": 3000,
        "reward_tokens": (280, 520),
        "reward_xp": (160, 320),
        "description": "A hot volcanic route for stronger dragons. High risk, high reward.",
    },
    "sky": {
        "name": "Sky Islands",
        "emoji": "☁️",
        "minutes": 90,
        "min_xp": 6000,
        "reward_tokens": (420, 850),
        "reward_xp": (250, 520),
        "description": "Floating islands above the clouds with legendary discoveries.",
    },
}

DISCOVERIES = [
    "found a glowing feather",
    "chased a strange butterfly",
    "dug up an old coin",
    "found claw marks from another dragon",
    "heard a mysterious song in the distance",
    "brought home a shiny stone",
    "met a tiny forest spirit",
    "found old guild markings carved into stone",
]

FAIL_LINES = [
    "came back tired and empty-clawed",
    "got scared by strange noises and returned early",
    "lost the trail and came home confused",
    "spent the whole adventure chasing its own tail",
]

def _now():
    return datetime.now(timezone.utc)

def _parse(value):
    return datetime.fromisoformat(value)

def active_adventure(guild_id: int):
    with db_session(row_factory=True) as con:
        cur = con.cursor()
        cur.execute(
            "SELECT * FROM adventures WHERE guild_id=? AND claimed=0",
            (guild_id,)
        )
        return cur.fetchone()

def available_adventures(guild_id: int):
    d = get_dragon(guild_id)
    unlocked = []

    for key, adv in ADVENTURES.items():
        if d["xp"] >= adv["min_xp"]:
            unlocked.append((key, adv))

    return unlocked

def start_adventure(guild_id: int, user_id: int, area_key: str):
    def work():
        if area_key not in ADVENTURES:
            return False, "Unknown adventure."

        d = get_dragon(guild_id)
        adv = ADVENTURES[area_key]

        if d["xp"] < adv["min_xp"]:
            return False, f"This adventure requires **{adv['min_xp']} dragon XP**."

        existing = active_adventure(guild_id)
        if existing:
            returns = _parse(existing["returns_at"])
            mins = max(1, int((returns - _now()).total_seconds() // 60))
            return False, f"🐉 The dragon is already on an adventure and returns in about **{mins} minutes**."

        # Research bonus: Dragon Library reduces adventure duration a little.
        minutes = adv["minutes"]
        if has_research(guild_id, "dragon_library"):
            minutes = max(5, int(minutes * 0.85))

        returns_at = _now() + timedelta(minutes=minutes)

        with db_session() as con:
            cur = con.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO adventures
                (guild_id, user_id, area_key, started_at, returns_at, claimed)
                VALUES (?, ?, ?, ?, ?, 0)
                """,
                (guild_id, user_id, area_key, _now().isoformat(), returns_at.isoformat())
            )
            cur.execute(
                """
                UPDATE dragon
                SET pose=?,
                    energy=max(0, energy-10),
                    dragon_message=?,
                    last_action_text=?
                WHERE guild_id=?
                """,
                (
                    "adventuring",
                    f"I am exploring the {adv['name']}!",
                    f"{adv['emoji']} The dragon left for **{adv['name']}** and will return soon.",
                    guild_id,
                )
            )
            add_memory_tx(cur, guild_id, f"The dragon left for an adventure in {adv['name']}.")

        return True, f"{adv['emoji']} Adventure started: **{adv['name']}**. The dragon returns in about **{minutes} minutes**."

    return execute_with_retry(work)

def claim_adventure(guild_id: int, user):
    def work():
        adventure = active_adventure(guild_id)

        if not adventure:
            return False, "There is no active adventure to claim."

        returns_at = _parse(adventure["returns_at"])
        if _now() < returns_at:
            mins = max(1, int((returns_at - _now()).total_seconds() // 60))
            return False, f"⏳ The dragon is still adventuring. Return in about **{mins} minutes**."

        adv = ADVENTURES[adventure["area_key"]]
        failed = random.random() < 0.15

        if failed:
            tokens = 0
            xp = random.randint(3, 15)
            result_line = random.choice(FAIL_LINES)
            message = f"The dragon {result_line}."
        else:
            tokens = random.randint(*adv["reward_tokens"])
            xp = random.randint(*adv["reward_xp"])
            discovery = random.choice(DISCOVERIES)
            message = f"The dragon {discovery} and brought treasure home."

        with db_session() as con:
            cur = con.cursor()

            cur.execute(
                "UPDATE adventures SET claimed=1 WHERE guild_id=?",
                (guild_id,)
            )

            cur.execute(
                """
                UPDATE dragon
                SET guild_tokens=guild_tokens+?,
                    lifetime_guild_tokens=lifetime_guild_tokens+?,
                    xp=xp+?,
                    energy=max(0, energy-15),
                    happiness=min(100, happiness+5),
                    pose=?,
                    visual_event=?,
                    dragon_message=?,
                    last_action_text=?
                WHERE guild_id=?
                """,
                (
                    tokens,
                    tokens,
                    xp,
                    "celebrating" if not failed else "sad",
                    "adventure",
                    message,
                    f"{adv['emoji']} **{user.display_name}** welcomed the dragon back from **{adv['name']}**.",
                    guild_id,
                )
            )

            cur.execute(
                """
                INSERT INTO memories (guild_id, text, created_at)
                VALUES (?, ?, ?)
                """,
                (
                    guild_id,
                    f"Adventure: {adv['name']} — {message}",
                    _now().isoformat()
                )
            )

        add_guild_level_xp(guild_id, max(1, tokens // 3) + xp)

        if failed:
            return True, f"⚠️ **Adventure complete:** {message}\nReward: **{xp} XP**, **0 Guild Tokens**."

        return True, f"🎒 **Adventure complete:** {message}\nReward: **{xp} XP** and **{tokens} Guild Tokens**."

    return execute_with_retry(work)

def adventure_status_text(guild_id: int):
    adventure = active_adventure(guild_id)

    if not adventure:
        return "🐉 The dragon is not currently on an adventure."

    adv = ADVENTURES[adventure["area_key"]]
    returns_at = _parse(adventure["returns_at"])

    if _now() >= returns_at:
        return f"{adv['emoji']} The dragon has returned from **{adv['name']}** and is waiting to be claimed."

    mins = max(1, int((returns_at - _now()).total_seconds() // 60))
    return f"{adv['emoji']} The dragon is exploring **{adv['name']}** and returns in about **{mins} minutes**."

def make_adventure_embed(guild_id: int):
    d = get_dragon(guild_id)
    stage, emoji = get_stage(d["xp"])

    embed = discord.Embed(
        title="🗺️ Dragon Adventures",
        description=(
            f"Send the guild dragon on adventures to find XP, Guild Tokens and memories.\n\n"
            f"Current dragon XP: **{d['xp']}**\n"
            f"Stage: **{emoji} {stage}**\n\n"
            f"{adventure_status_text(guild_id)}"
        ),
        color=0x7B2CFF
    )

    for key, adv in ADVENTURES.items():
        locked = d["xp"] < adv["min_xp"]
        status = f"🔒 Requires {adv['min_xp']} XP" if locked else f"✅ {adv['minutes']} min"
        embed.add_field(
            name=f"{adv['emoji']} {adv['name']} — {status}",
            value=adv["description"],
            inline=False
        )

    return embed
