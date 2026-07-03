import random
from datetime import datetime, timezone, timedelta
from database import connect, get_dragon
from utils import is_night_utc, current_season, clamp, get_stage
from memories import add_memory

IDLE_POSES_DAY = [
    "waiting",
    "looking around",
    "stretching",
    "guarding the lair",
    "playing",
]

IDLE_POSES_NIGHT = [
    "sleeping",
    "guarding the lair",
    "looking around",
]

CARE_REQUEST_COOLDOWN_HOURS = 6

SEASONAL_LINES = {
    "Spring": [
        "I can smell fresh flowers near the cave.",
        "Spring makes the lair feel alive.",
        "Tiny flowers are growing near my nest.",
    ],
    "Summer": [
        "The warm air makes me want to fly.",
        "Summer sunlight feels nice on my scales.",
        "Is it too warm for a tiny fire breath?",
    ],
    "Autumn": [
        "Leaves are dancing outside the cave.",
        "Autumn winds make the cave sound mysterious.",
        "I found a golden leaf near my nest.",
    ],
    "Winter": [
        "The cave feels cold today...",
        "I like curling up when snow falls outside.",
        "My breath looks like little clouds.",
    ],
    "Halloween": [
        "Something spooky moved in the shadows...",
        "I found a pumpkin near the lair entrance.",
        "Do dragons get Halloween treats too?",
    ],
    "Christmas": [
        "The lair feels magical today.",
        "I hope someone brings shiny presents.",
        "Snow and warm fires make the best dragon naps.",
    ],
}

LIVING_LINES = {
    "wake": [
        "Good morning, keepers!",
        "I woke up and stretched my tiny wings.",
        "A new day begins in the lair.",
    ],
    "sleep": [
        "I am getting sleepy...",
        "I curled up in my nest.",
        "Good night, keepers.",
    ],
    "hungry": [
        "My tummy is rumbling...",
        "Could someone bring me food?",
        "I am trying to be brave, but I am hungry.",
    ],
    "messy": [
        "My scales feel dusty...",
        "The lair could use some cleaning.",
        "I stepped in something sticky again.",
    ],
    "lonely": [
        "Is anyone visiting the lair today?",
        "The cave feels quiet...",
        "I miss my keepers.",
    ],
    "happy": [
        "I love this guild.",
        "This place feels like home.",
        "I feel safe with my keepers.",
    ],
    "milestone": [
        "I feel myself growing stronger.",
        "Something inside me is changing...",
        "Every day, I become more like a real dragon.",
    ],
}

def _parse_time(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None

def _can_send_care_request(d):
    last = _parse_time(d["last_care_request"])
    if not last:
        return True
    return datetime.now(timezone.utc) - last >= timedelta(hours=CARE_REQUEST_COOLDOWN_HOURS)

def choose_living_state(d):
    night = is_night_utc()
    season = current_season()

    pose = random.choice(IDLE_POSES_NIGHT if night else IDLE_POSES_DAY)
    sleeping = 1 if night and random.random() < 0.75 else 0

    message = None
    reason = "idle"

    if sleeping:
        pose = "sleeping"
        message = random.choice(LIVING_LINES["sleep"])
        reason = "sleep"
    elif d["hunger"] < 25:
        pose = "sad"
        message = random.choice(LIVING_LINES["hungry"])
        reason = "hungry"
    elif d["cleanliness"] < 25:
        pose = "sad"
        message = random.choice(LIVING_LINES["messy"])
        reason = "messy"
    elif d["happiness"] < 30:
        pose = "sad"
        message = random.choice(LIVING_LINES["lonely"])
        reason = "lonely"
    elif d["bond"] > 80 and random.random() < 0.35:
        pose = "bonding"
        message = random.choice(LIVING_LINES["happy"])
        reason = "happy"
    elif random.random() < 0.30:
        message = random.choice(SEASONAL_LINES.get(season, SEASONAL_LINES["Summer"]))
        reason = "season"
    else:
        message = random.choice([
            "I moved around the lair a little.",
            "I watched the cave entrance quietly.",
            "I listened to the sounds outside.",
            "I scratched the ground near my nest.",
            "I looked at the guild treasure pile.",
        ])

    return pose, sleeping, message, reason

def living_update(guild_id: int):
    d = get_dragon(guild_id)
    pose, sleeping, message, reason = choose_living_state(d)
    season = current_season()

    con = connect()
    cur = con.cursor()

    cur.execute("""
        UPDATE dragon
        SET pose=?,
            sleeping=?,
            dragon_message=?,
            last_living_update=?,
            last_action_text=?
        WHERE guild_id=?
    """, (
        pose,
        sleeping,
        message,
        datetime.now(timezone.utc).isoformat(),
        f"🐉 The dragon is living in the lair. Season: **{season}**.",
        guild_id,
    ))

    con.commit()
    con.close()

    return reason, message

def should_request_care(guild_id: int):
    d = get_dragon(guild_id)

    if not _can_send_care_request(d):
        return False, None

    if d["hunger"] < 20:
        return True, "🍖 The dragon is very hungry and is asking for food."
    if d["cleanliness"] < 20:
        return True, "🛁 The dragon is very dirty and is asking for help."
    if d["happiness"] < 20:
        return True, "💔 The dragon feels lonely and wants someone to visit."
    if d["energy"] < 15:
        return True, "😴 The dragon is exhausted and wants to rest."

    return False, None

def mark_care_request_sent(guild_id: int):
    con = connect()
    cur = con.cursor()
    cur.execute("UPDATE dragon SET last_care_request=? WHERE guild_id=?", (datetime.now(timezone.utc).isoformat(), guild_id))
    con.commit()
    con.close()

def check_growth_memory(guild_id: int):
    d = get_dragon(guild_id)
    stage, _ = get_stage(d["xp"])
    # Lightweight memory only for round XP milestones.
    if d["xp"] > 0 and d["xp"] % 1000 < 10:
        add_memory(guild_id, f"The dragon felt stronger around {d['xp']} XP while still in stage {stage}.")
