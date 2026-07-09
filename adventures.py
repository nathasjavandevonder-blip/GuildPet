import random
from datetime import datetime, timezone, timedelta
import discord
from database import db_session, execute_with_retry, get_dragon, add_memory_tx
from progression import has_research, add_guild_level_xp
from utils import get_stage
from rpg import (
    add_inventory_item, progress_quest, set_quest_progress, ITEMS, RARITY_EMOJI,
    simulate_combat, compute_dragon_stats, get_lair_level
)

ADVENTURES = {
    "forest": {"name": "Ancient Forest", "emoji": "🌲", "minutes": 10, "min_xp": 0, "energy_cost": 8,
        "reward_tokens": (40, 100), "reward_xp": (25, 70), "loot": ["moon_berry", "sweet_melon", "shiny_scale", "ancient_coin", "training_collar"],
        "monsters": [{"name": "Wild Boar", "hp": 24, "attack": 7, "defense": 2}, {"name": "Vine Sprite", "hp": 20, "attack": 6, "defense": 3}, {"name": "Forest Imp", "hp": 18, "attack": 8, "defense": 1}],
        "description": "A safe route with berries, tiny monsters and beginner loot."},
    "lake": {"name": "Crystal Lake", "emoji": "🌊", "minutes": 20, "min_xp": 250*55, "energy_cost": 10,
        "reward_tokens": (80, 170), "reward_xp": (55, 120), "loot": ["moon_berry", "energy_biscuit", "crystal_shard", "ancient_coin", "scholar_charm"],
        "monsters": [{"name": "Lake Serpent", "hp": 34, "attack": 9, "defense": 4}, {"name": "Crystal Crab", "hp": 40, "attack": 7, "defense": 6}, {"name": "Mist Wisp", "hp": 26, "attack": 11, "defense": 2}],
        "description": "Crystals, mist and magical fishbones. Balanced rewards."},
    "ruins": {"name": "Ancient Ruins", "emoji": "🏛️", "minutes": 30, "min_xp": 750*55, "energy_cost": 12,
        "reward_tokens": (130, 280), "reward_xp": (90, 180), "loot": ["ancient_coin", "crystal_shard", "storm_feather", "forest_cloak", "scholar_charm"],
        "monsters": [{"name": "Stone Guardian", "hp": 50, "attack": 12, "defense": 8}, {"name": "Dust Wraith", "hp": 38, "attack": 15, "defense": 4}, {"name": "Relic Spider", "hp": 42, "attack": 13, "defense": 5}],
        "description": "Old rooms, traps and relic guardians. Good equipment chance."},
    "mountains": {"name": "Storm Mountains", "emoji": "⛰️", "minutes": 45, "min_xp": 1500*55, "energy_cost": 15,
        "reward_tokens": (210, 420), "reward_xp": (140, 280), "loot": ["storm_feather", "crystal_shard", "storm_wings", "frost_pearl", "dragon_crown"],
        "monsters": [{"name": "Thunder Roc", "hp": 62, "attack": 17, "defense": 8}, {"name": "Mountain Troll", "hp": 80, "attack": 16, "defense": 10}, {"name": "Storm Drake", "hp": 70, "attack": 19, "defense": 9}],
        "description": "Harder fights with rare relics and wing equipment."},
    "volcano": {"name": "Fire Volcano", "emoji": "🌋", "minutes": 60, "min_xp": 3000*55, "energy_cost": 18,
        "reward_tokens": (330, 620), "reward_xp": (220, 420), "loot": ["fire_heart", "ember_meat", "crystal_shard", "dragon_crown", "void_artifact"],
        "monsters": [{"name": "Lava Hound", "hp": 78, "attack": 21, "defense": 11}, {"name": "Ash Golem", "hp": 95, "attack": 18, "defense": 15}, {"name": "Fire Wyvern", "hp": 88, "attack": 24, "defense": 12}],
        "description": "High risk. Big combat rewards and legendary equipment chance."},
    "frost": {"name": "Frozen Peaks", "emoji": "❄️", "minutes": 75, "min_xp": 4500*55, "energy_cost": 20,
        "reward_tokens": (390, 760), "reward_xp": (260, 520), "loot": ["frost_pearl", "storm_feather", "sunstone", "dragon_crown", "void_artifact"],
        "monsters": [{"name": "Frost Wolf", "hp": 86, "attack": 23, "defense": 13}, {"name": "Ice Golem", "hp": 110, "attack": 20, "defense": 18}, {"name": "Glacier Spirit", "hp": 90, "attack": 27, "defense": 11}],
        "description": "Endurance route with strong defense loot."},
    "void": {"name": "Void Gate", "emoji": "🌌", "minutes": 90, "min_xp": 6000*55, "energy_cost": 22,
        "reward_tokens": (520, 950), "reward_xp": (350, 700), "loot": ["void_gem", "void_artifact", "dragon_crown", "sunstone", "fire_heart"],
        "monsters": [{"name": "Voidling", "hp": 95, "attack": 28, "defense": 13}, {"name": "Star Eater", "hp": 120, "attack": 30, "defense": 16}, {"name": "Ancient Shadow", "hp": 140, "attack": 32, "defense": 18}],
        "description": "Mythic route. Very dangerous, very profitable."},
}

DISCOVERIES = [
    "found a hidden path marked by old dragon claws", "dug up a sealed treasure box",
    "followed glowing footprints to a buried relic", "rescued a tiny forest spirit",
    "found an abandoned keeper camp", "discovered a mural about elder dragons",
    "brought home a crystal still warm with magic", "found old guild markings carved into stone",
]
FAIL_LINES = [
    "came back tired and empty-clawed", "got scared by strange noises and returned early",
    "lost the trail and came home confused", "spent too long chasing fireflies and forgot the mission",
]

def _now(): return datetime.now(timezone.utc)
def _parse(value): return datetime.fromisoformat(value)

def active_adventure(guild_id: int):
    with db_session(row_factory=True) as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM adventures WHERE guild_id=? AND claimed=0", (guild_id,))
        return cur.fetchone()

def available_adventures(guild_id: int):
    d = get_dragon(guild_id)
    return [(k, a) for k, a in ADVENTURES.items() if d["xp"] >= a["min_xp"]]

def start_adventure(guild_id: int, user_id: int, area_key: str):
    def work():
        if area_key not in ADVENTURES:
            return False, "Unknown adventure."
        d = get_dragon(guild_id)
        adv = ADVENTURES[area_key]
        if d["xp"] < adv["min_xp"]:
            return False, f"This adventure requires **{adv['min_xp']} dragon XP**."
        if d["energy"] < adv["energy_cost"]:
            return False, f"⚡ The dragon needs at least **{adv['energy_cost']} energy**. Let it rest first."
        existing = active_adventure(guild_id)
        if existing:
            mins = max(1, int((_parse(existing["returns_at"]) - _now()).total_seconds() // 60))
            return False, f"🐉 The dragon is already adventuring and returns in about **{mins} minutes**."
        minutes = adv["minutes"]
        if has_research(guild_id, "dragon_library"):
            minutes = max(5, int(minutes * 0.85))
        library = get_lair_level(guild_id, "library")
        if library:
            minutes = max(5, int(minutes * (1 - min(0.20, library * 0.03))))
        returns_at = _now() + timedelta(minutes=minutes)
        with db_session() as con:
            cur = con.cursor()
            cur.execute("""INSERT OR REPLACE INTO adventures
                (guild_id,user_id,area_key,started_at,returns_at,claimed)
                VALUES (?,?,?,?,?,0)""", (guild_id, user_id, area_key, _now().isoformat(), returns_at.isoformat()))
            cur.execute("""UPDATE dragon SET pose=?, energy=max(0,energy-?), dragon_message=?, last_action_text=? WHERE guild_id=?""",
                ("adventuring", adv["energy_cost"], f"I am exploring the {adv['name']}!", f"{adv['emoji']} The dragon left for **{adv['name']}** and will return soon.", guild_id))
            add_memory_tx(cur, guild_id, f"The dragon left for an adventure in {adv['name']}.")
        return True, f"{adv['emoji']} Adventure started: **{adv['name']}**. The dragon returns in about **{minutes} minutes**."
    return execute_with_retry(work)

def _loot_roll(adv, boss=False, won=True):
    pool = list(adv["loot"])
    if boss:
        pool += [k for k, v in ITEMS.items() if v.get("type") == "Equipment"]
    if not won:
        pool = ["moon_berry", "shiny_scale", "ancient_coin"]
    key = random.choice(pool)
    item = ITEMS.get(key, {"name": key.replace("_", " ").title(), "rarity": "Common", "type": "Material"})
    qty = 1
    if item["rarity"] in ["Common", "Uncommon"] and item.get("type") != "Equipment":
        qty = random.randint(1, 3)
    return key, item, qty

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
        d = get_dragon(guild_id)
        monster = random.choice(adv["monsters"])
        boss = random.random() < min(0.20, 0.07 + compute_dragon_stats(guild_id)["luck"] / 400)
        won, hp_left, rounds = simulate_combat(guild_id, monster, boss=boss)
        discovery = random.choice(DISCOVERIES if won else FAIL_LINES)

        if won:
            tokens = random.randint(*adv["reward_tokens"])
            xp = random.randint(*adv["reward_xp"])
            if boss:
                tokens = int(tokens * 1.8); xp = int(xp * 1.6)
            key, item, qty = _loot_roll(adv, boss=boss, won=True)
            add_inventory_item(guild_id, key, qty, 0)
            icon = RARITY_EMOJI.get(item["rarity"], "⚪")
            loot_text = f"{icon} **{item['name']}** ×{qty} (`{item['rarity']} {item['type']}`)"
            outcome = f"won against **{'Boss ' if boss else ''}{monster['name']}** and {discovery}"
            progress_quest(guild_id, "combat_daily", 1)
        else:
            tokens = random.randint(5, 25)
            xp = random.randint(10, 35)
            key, item, qty = _loot_roll(adv, boss=False, won=False)
            add_inventory_item(guild_id, key, qty, 0)
            icon = RARITY_EMOJI.get(item["rarity"], "⚪")
            loot_text = f"{icon} **{item['name']}** ×{qty} (`comfort loot`)"
            outcome = f"lost to **{monster['name']}**, but {discovery}"

        combat_log = "\n".join(rounds[:6])
        message = f"The dragon {outcome}."
        reward_text = f"+{xp} XP, +{tokens} Guild Tokens, {loot_text}"
        with db_session() as con:
            cur = con.cursor()
            cur.execute("UPDATE adventures SET claimed=1 WHERE guild_id=?", (guild_id,))
            cur.execute("""UPDATE dragon SET guild_tokens=guild_tokens+?, lifetime_guild_tokens=lifetime_guild_tokens+?, xp=xp+?,
                energy=max(0,energy-4), happiness=min(100,happiness+?), pose=?, visual_event=?, dragon_message=?, last_action_text=? WHERE guild_id=?""",
                (tokens, tokens, xp, 6 if won else 2, "celebrating" if won else "sad", "adventure", message,
                 f"{adv['emoji']} **{user.display_name}** welcomed the dragon back from **{adv['name']}**.", guild_id))
            cur.execute("INSERT INTO memories (guild_id,text,created_at) VALUES (?,?,?)", (guild_id, f"Adventure: {adv['name']} — {message}", _now().isoformat()))
            cur.execute("INSERT INTO adventure_log (guild_id,user_id,area_key,result,reward_text,created_at) VALUES (?,?,?,?,?,?)",
                (guild_id, user.id, adventure["area_key"], message, reward_text, _now().isoformat()))
        add_guild_level_xp(guild_id, max(1, tokens // 3) + xp)
        progress_quest(guild_id, "adventure_daily", 1)
        set_quest_progress(guild_id, "bond_story", d["bond"])
        result_icon = "🏆" if won else "⚠️"
        return True, f"{result_icon} **Adventure complete: {adv['name']}**\n{message}\n\n**Combat**\n{combat_log}\n\n**Rewards**\n{reward_text}\n❤️ HP left: **{hp_left}**"
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
    status = adventure_status_text(guild_id)
    stage, _ = get_stage(d["xp"])
    stats = compute_dragon_stats(guild_id)
    embed = discord.Embed(
        title="🗺️ Guild Dragon Adventures",
        description=(
            f"**Stage:** {stage}\n**Energy:** {d['energy']}%\n"
            f"❤️ HP `{stats['health']}`  💪 STR `{stats['strength']}`  🛡 DEF `{stats['defense']}`  ⚡ AGI `{stats['agility']}`  🍀 LUCK `{stats['luck']}`\n\n"
            f"{status}\n\nChoose a route below. Adventures now include combat, loot, boss chance and quest progress."
        ),
        color=0x5865F2,
    )
    for key, adv in ADVENTURES.items():
        lock = "✅" if d["xp"] >= adv["min_xp"] else "🔒"
        monsters = ", ".join(m["name"] for m in adv["monsters"][:3])
        embed.add_field(
            name=f"{lock} {adv['emoji']} {adv['name']}",
            value=f"{adv['description']}\nTime: **{adv['minutes']}m** • Energy: **{adv['energy_cost']}** • XP req: **{adv['min_xp']}**\nEnemies: {monsters}",
            inline=False,
        )
    return embed
