import random
from datetime import datetime, timezone
from database import connect, get_dragon

TRAITS = ["Friendly", "Brave", "Curious", "Playful", "Wise", "Protective", "Lazy", "Greedy"]

MOOD_COLORS = {
    "Happy": 0x8be56f,
    "Excited": 0xffcc4d,
    "Sleepy": 0x8ea7ff,
    "Hungry": 0xff8a4d,
    "Lonely": 0x9b8cff,
    "Proud": 0xd6a84f,
    "Messy": 0x8b6f47,
    "Curious": 0xb76cff,
}

def now():
    return datetime.now(timezone.utc).isoformat()

def init_v5():
    con = connect()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS dragon_personality_scores (
        guild_id INTEGER,
        trait TEXT,
        score INTEGER DEFAULT 0,
        PRIMARY KEY (guild_id, trait)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS dragon_relationships (
        guild_id INTEGER,
        user_id INTEGER,
        username TEXT,
        bond INTEGER DEFAULT 0,
        last_interaction TEXT,
        PRIMARY KEY (guild_id, user_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS dragon_contributions_v5 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER,
        user_id INTEGER,
        username TEXT,
        action TEXT,
        amount INTEGER DEFAULT 1,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS dragon_memories_v5 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER,
        user_id INTEGER,
        username TEXT,
        memory_type TEXT,
        memory_text TEXT,
        importance INTEGER DEFAULT 1,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS lair_rooms_v5 (
        guild_id INTEGER,
        room_key TEXT,
        room_name TEXT,
        level INTEGER DEFAULT 0,
        PRIMARY KEY (guild_id, room_key)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS decorations_v5 (
        guild_id INTEGER,
        decoration_key TEXT,
        decoration_name TEXT,
        equipped INTEGER DEFAULT 0,
        created_at TEXT,
        PRIMARY KEY (guild_id, decoration_key)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS world_events_v5 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER,
        event_name TEXT,
        event_text TEXT,
        reward_text TEXT,
        created_at TEXT
    )
    """)

    for trait in TRAITS:
        cur.execute(
            "INSERT OR IGNORE INTO dragon_personality_scores (guild_id, trait, score) SELECT guild_id, ?, 0 FROM dragon",
            (trait,),
        )

    con.commit()
    con.close()

def add_memory(guild_id, text, user=None, memory_type="General", importance=1):
    init_v5()
    con = connect()
    cur = con.cursor()
    cur.execute(
        """INSERT INTO dragon_memories_v5
        (guild_id, user_id, username, memory_type, memory_text, importance, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            guild_id,
            user.id if user else None,
            user.display_name if user else None,
            memory_type,
            text,
            importance,
            now(),
        ),
    )
    con.commit()
    con.close()

def change_trait(guild_id, trait, amount):
    init_v5()
    con = connect()
    cur = con.cursor()
    cur.execute(
        """INSERT INTO dragon_personality_scores (guild_id, trait, score)
        VALUES (?, ?, ?)
        ON CONFLICT(guild_id, trait) DO UPDATE SET score = score + excluded.score""",
        (guild_id, trait, amount),
    )
    con.commit()
    con.close()

def record_contribution(guild_id, user, action, amount=1):
    init_v5()
    con = connect()
    cur = con.cursor()

    cur.execute(
        """INSERT INTO dragon_contributions_v5
        (guild_id, user_id, username, action, amount, created_at)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (guild_id, user.id, user.display_name, action, amount, now()),
    )

    cur.execute(
        """INSERT INTO dragon_relationships
        (guild_id, user_id, username, bond, last_interaction)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(guild_id, user_id) DO UPDATE SET
            username=excluded.username,
            bond=bond + excluded.bond,
            last_interaction=excluded.last_interaction""",
        (guild_id, user.id, user.display_name, amount, now()),
    )

    con.commit()
    con.close()

    trait_map = {
        "feed": "Friendly",
        "play": "Playful",
        "train": "Brave",
        "clean": "Wise",
        "rest": "Lazy",
        "bond": "Friendly",
        "pet": "Friendly",
        "praise": "Proud",
        "encourage": "Protective",
        "scold": "Brave",
    }
    change_trait(guild_id, trait_map.get(action, "Curious"), amount)

    if random.random() < 0.12:
        add_memory(
            guild_id,
            f"{user.display_name} spent time with me and helped shape who I am.",
            user=user,
            memory_type="Relationship",
            importance=2,
        )

def calculate_mood(guild_id):
    d = get_dragon(guild_id)
    if d["hunger"] < 25:
        return "Hungry"
    if d["cleanliness"] < 25:
        return "Messy"
    if d["energy"] < 20:
        return "Sleepy"
    if d["bond"] >= 80 and d["happiness"] >= 75:
        return "Proud"
    if d["happiness"] >= 80:
        return "Happy"
    return "Curious"

def dominant_personality(guild_id):
    init_v5()
    con = connect()
    cur = con.cursor()
    cur.execute(
        """SELECT trait, score FROM dragon_personality_scores
        WHERE guild_id=?
        ORDER BY score DESC, trait ASC
        LIMIT 1""",
        (guild_id,),
    )
    row = cur.fetchone()
    con.close()
    return row[0] if row and row[1] > 0 else "Curious"

def update_v5_state(guild_id):
    mood = calculate_mood(guild_id)
    personality = dominant_personality(guild_id)
    con = connect()
    cur = con.cursor()
    cur.execute(
        "UPDATE dragon SET mood=?, personality=? WHERE guild_id=?",
        (mood, personality, guild_id),
    )
    con.commit()
    con.close()
    return mood, personality

def talk_response(guild_id, user):
    init_v5()
    mood, personality = update_v5_state(guild_id)

    con = connect()
    cur = con.cursor()
    cur.execute(
        "SELECT bond FROM dragon_relationships WHERE guild_id=? AND user_id=?",
        (guild_id, user.id),
    )
    row = cur.fetchone()
    personal_bond = row[0] if row else 0
    con.close()

    responses = {
        "Friendly": [
            f"{user.display_name}, I like when you visit me.",
            "This guild feels like home.",
            "I remember the keepers who care for me.",
        ],
        "Brave": [
            "I will protect this guild.",
            "One day my roar will shake the sky.",
            "Training makes my fire stronger.",
        ],
        "Curious": [
            "I wonder what lies beyond the cave.",
            "Do you think there are more crystals outside?",
            "Tell me more about the guild.",
        ],
        "Playful": [
            "Can we play again?",
            "I almost caught my own tail today.",
            "The lair feels boring without the guild.",
        ],
        "Wise": [
            "Small actions become great memories.",
            "A guild grows strongest when everyone helps.",
            "I remember more than you think.",
        ],
        "Protective": [
            "No one will harm this guild while I am here.",
            "I watch over the lair.",
            "Your enemies should fear my wings.",
        ],
        "Lazy": [
            "Five more minutes...",
            "The nest is very comfortable today.",
            "Wake me when snacks arrive.",
        ],
        "Greedy": [
            "I smelled treasure nearby.",
            "Gold makes a lair feel warmer.",
            "A bigger treasure room would be nice.",
        ],
    }

    text = random.choice(responses.get(personality, responses["Curious"]))

    if mood == "Hungry":
        text += "\n\nAlso... my tummy is rumbling."
    elif mood == "Sleepy":
        text += "\n\nI am getting sleepy."
    elif mood == "Messy":
        text += "\n\nMy lair could use some cleaning."
    elif mood == "Proud":
        text += "\n\nI feel proud of this guild."

    if personal_bond >= 10:
        text += f"\n\nI know you well, {user.display_name}. You have helped me many times."

    return text, mood, personality, personal_bond

def get_top_contributors(guild_id, limit=10):
    init_v5()
    con = connect()
    cur = con.cursor()
    cur.execute(
        """SELECT user_id, username, SUM(amount) total
        FROM dragon_contributions_v5
        WHERE guild_id=?
        GROUP BY user_id, username
        ORDER BY total DESC
        LIMIT ?""",
        (guild_id, limit),
    )
    rows = cur.fetchall()
    con.close()
    return rows

def get_memories(guild_id, limit=10):
    init_v5()
    con = connect()
    cur = con.cursor()
    cur.execute(
        """SELECT memory_text, memory_type, username, created_at
        FROM dragon_memories_v5
        WHERE guild_id=?
        ORDER BY importance DESC, id DESC
        LIMIT ?""",
        (guild_id, limit),
    )
    rows = cur.fetchall()
    con.close()
    return rows

def upgrade_lair_room(guild_id, room_key):
    init_v5()
    rooms = {
        "nest": "Dragon Nest",
        "crystals": "Crystal Garden",
        "treasure": "Treasure Room",
        "library": "Memory Library",
        "training": "Training Ground",
        "forge": "Dragon Forge",
    }
    room_name = rooms.get(room_key.lower())
    if not room_name:
        return None

    con = connect()
    cur = con.cursor()
    cur.execute(
        """INSERT INTO lair_rooms_v5 (guild_id, room_key, room_name, level)
        VALUES (?, ?, ?, 1)
        ON CONFLICT(guild_id, room_key) DO UPDATE SET level = level + 1""",
        (guild_id, room_key.lower(), room_name),
    )
    con.commit()
    con.close()
    return room_name

def get_lair(guild_id):
    init_v5()
    con = connect()
    cur = con.cursor()
    cur.execute(
        "SELECT room_name, level FROM lair_rooms_v5 WHERE guild_id=? ORDER BY level DESC, room_name",
        (guild_id,),
    )
    rows = cur.fetchall()
    con.close()
    return rows

def create_world_event(guild_id):
    init_v5()
    events = [
        ("Crystal Growth", "New crystals are growing inside the lair.", "+2 Curious personality"),
        ("Wandering Merchant", "A merchant passed by and admired the dragon.", "+2 Greedy personality"),
        ("Meteor Shower", "The sky lit up above the cave.", "+2 Wise personality"),
        ("Goblin Trouble", "A goblin tried to sneak into the treasure room.", "+2 Brave personality"),
        ("Quiet Night", "The lair was peaceful and warm.", "+2 Friendly personality"),
        ("Dragon Festival", "The guild celebrated the dragon together.", "+2 Playful personality"),
    ]
    name, text, reward = random.choice(events)

    trait = {
        "Crystal Growth": "Curious",
        "Wandering Merchant": "Greedy",
        "Meteor Shower": "Wise",
        "Goblin Trouble": "Brave",
        "Quiet Night": "Friendly",
        "Dragon Festival": "Playful",
    }[name]
    change_trait(guild_id, trait, 2)

    con = connect()
    cur = con.cursor()
    cur.execute(
        """INSERT INTO world_events_v5
        (guild_id, event_name, event_text, reward_text, created_at)
        VALUES (?, ?, ?, ?, ?)""",
        (guild_id, name, text, reward, now()),
    )
    con.commit()
    con.close()

    add_memory(guild_id, f"{name}: {text}", memory_type="World Event", importance=2)
    return name, text, reward
