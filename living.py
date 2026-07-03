import random
from datetime import datetime, timezone, timedelta
from database import connect, get_dragon
from utils import is_night_utc, current_season, clamp, get_stage
from memories import add_memory
from traits import ensure_trait, trait_quote

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

WORLD_EVENTS = [
    ("None", "The lair is calm."),
    ("Rainbow", "🌈 A rainbow shines near the cave."),
    ("Butterflies", "🦋 Butterflies flutter around the dragon."),
    ("Mushrooms", "🍄 Small glowing mushrooms grew nearby."),
    ("Full Moon", "🌕 The moonlight fills the cave."),
    ("Meteor Shower", "⭐ A meteor shower lights the sky."),
    ("Heavy Rain", "🌧️ Heavy rain falls outside the lair."),
    ("Warm Breeze", "🍃 A warm breeze moves through the cave."),
    ("Fresh Footprints", "🐾 Fresh footprints surround the nest."),
    ("Mysterious Feather", "🪶 A mysterious feather appeared near the dragon."),
    ("Fruit Gift", "🍎 Someone left fruit near the cave."),
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

MOOD_LINES = {
    "Hungry": [
        "My stomach is making funny noises...",
        "Could someone bring food?",
        "I am trying to be brave, but I am hungry.",
    ],
    "Messy": [
        "My scales feel dusty...",
        "The lair could use some cleaning.",
        "I stepped in something sticky again.",
    ],
    "Sleepy": [
        "Five more minutes...",
        "I am getting sleepy.",
        "The nest looks very comfortable.",
    ],
    "Lonely": [
        "Where is everybody?",
        "The cave feels quiet...",
        "I miss my keepers.",
    ],
    "Happy": [
        "I love this guild.",
        "This place feels like home.",
        "I feel safe with my keepers.",
    ],
    "Excited": [
        "Let's explore!",
        "Something exciting could happen today.",
        "I feel like running around the lair!",
    ],
}

AFFECTION_EVENTS = [
    "🐉 The dragon nuzzles {name}.",
    "🐉 The dragon sits beside {name}.",
    "🐉 The dragon happily circles around {name}.",
    "🐉 The dragon rests its head near {name}.",
    "🐉 The dragon follows {name} around the lair.",
]

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

def dragon_mood_key(d):
    if d["hunger"] < 25:
        return "Hungry"
    if d["cleanliness"] < 25:
        return "Messy"
    if d["energy"] < 25:
        return "Sleepy"
    if d["happiness"] < 30:
        return "Lonely"
    if d["happiness"] > 85 and d["energy"] > 60:
        return "Excited"
    return "Happy"

def choose_world_event():
    # Most updates are calm, sometimes a world detail appears.
    if random.random() < 0.55:
        return ("None", "The lair is calm.")
    return random.choice(WORLD_EVENTS[1:])

def choose_living_state(guild_id: int, d):
    ensure_trait(guild_id)

    night = is_night_utc()
    season = current_season()
    mood_key = dragon_mood_key(d)

    pose = random.choice(IDLE_POSES_NIGHT if night else IDLE_POSES_DAY)
    sleeping = 1 if night and random.random() < 0.75 else 0

    if d["dragon_trait"] == "Lazy" and random.random() < 0.30:
        sleeping = 1
        pose = "sleeping"

    if sleeping:
        return "sleeping", 1, random.choice(MOOD_LINES["Sleepy"]), "sleep"

    if mood_key in ["Hungry", "Messy", "Sleepy", "Lonely"]:
        return "sad", 0, random.choice(MOOD_LINES[mood_key]), mood_key.lower()

    if random.random() < 0.22:
        return pose, 0, trait_quote(guild_id), "trait"

    if random.random() < 0.30:
        return pose, 0, random.choice(SEASONAL_LINES.get(season, SEASONAL_LINES["Summer"])), "season"

    return pose, 0, random.choice(MOOD_LINES.get(mood_key, MOOD_LINES["Happy"])), mood_key.lower()

def living_update(guild_id: int):
    d = get_dragon(guild_id)
    pose, sleeping, message, reason = choose_living_state(guild_id, d)
    world_event, world_text = choose_world_event()
    season = current_season()

    if world_event != "None" and random.random() < 0.70:
        message = world_text

    con = connect()
    cur = con.cursor()
    cur.execute("""
        UPDATE dragon
        SET pose=?,
            sleeping=?,
            world_event=?,
            dragon_message=?,
            last_living_update=?,
            last_action_text=?
        WHERE guild_id=?
    """, (
        pose,
        sleeping,
        world_event,
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

def affection_event_text(member_name: str):
    return random.choice(AFFECTION_EVENTS).format(name=member_name)
