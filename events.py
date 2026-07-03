import random
from datetime import datetime, timedelta, timezone
import discord
from database import connect
from dragon import add_player_reward

EVENTS = [
    ("mouse", "🐭 Mouse spotted!", "The dragon spotted a mouse running through the lair!"),
    ("treasure", "💎 Hidden treasure!", "The dragon found something shiny behind the nest."),
    ("merchant", "🧙 Mysterious merchant!", "A traveler offers a small gift to the first keeper."),
    ("storm", "🌧️ Storm in the lair!", "The dragon needs help before the cave gets too messy."),
    ("rare_meat", "🥩 Rare meat appeared!", "A rare piece of meat appeared near the dragon."),
]

def create_event_record(guild_id: int, event_type: str, message_id: int):
    expires = datetime.now(timezone.utc) + timedelta(minutes=15)
    con = connect()
    cur = con.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO events (guild_id, event_type, expires_at, claimed_by, message_id)
        VALUES (?, ?, ?, NULL, ?)
    """, (guild_id, event_type, expires.isoformat(), message_id))
    con.commit()
    con.close()

def claim_event(guild_id: int, user):
    con = connect()
    con.row_factory = __import__("sqlite3").Row
    cur = con.cursor()
    cur.execute("SELECT * FROM events WHERE guild_id=?", (guild_id,))
    event = cur.fetchone()

    if not event:
        con.close()
        return False, "This event is no longer active."
    if event["claimed_by"]:
        con.close()
        return False, "Someone already claimed this event."
    if datetime.now(timezone.utc) > datetime.fromisoformat(event["expires_at"]):
        con.close()
        return False, "This event expired."

    reward_tokens = random.randint(20, 50)
    reward_xp = random.randint(10, 30)

    cur.execute("UPDATE events SET claimed_by=? WHERE guild_id=?", (user.id, guild_id))
    cur.execute("""
        UPDATE dragon
        SET xp=xp+?, guild_tokens=guild_tokens+?, last_action_text=?, dragon_message=?, pose=?
        WHERE guild_id=?
    """, (reward_xp, reward_tokens, f"🎁 **{user.display_name}** claimed a random event reward!", "Treasure makes my lair feel special.", "celebrating", guild_id))
    con.commit()
    con.close()

    add_player_reward(guild_id, user.id, reward_tokens, reward_tokens, "event")
    return True, f"🎁 **{user.display_name}** claimed the event and won **{reward_tokens} tokens** + **{reward_xp} XP**!"

def random_event_embed():
    event_type, title, text = random.choice(EVENTS)
    embed = discord.Embed(
        title=title,
        description=text + "\n\nFirst person to claim gets a reward.\nThis event expires in **15 minutes**.",
        color=0x7B2CFF
    )
    return event_type, embed
