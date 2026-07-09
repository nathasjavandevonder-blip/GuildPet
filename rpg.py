from datetime import datetime, timezone
import random
from database import db_session, execute_with_retry, get_dragon
from utils import get_stage

RARITY_EMOJI = {
    "Common": "⚪", "Uncommon": "🟢", "Rare": "🔵", "Epic": "🟣",
    "Legendary": "🟠", "Mythic": "🔴"
}
RARITY_ORDER = ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythic"]

ITEMS = {
    # Food / consumables
    "moon_berry": {"name": "Moon Berry", "rarity": "Common", "type": "Food", "bonus": "+hunger", "score": 1},
    "sweet_melon": {"name": "Sweet Melon", "rarity": "Common", "type": "Food", "bonus": "+happiness", "score": 1},
    "energy_biscuit": {"name": "Energy Biscuit", "rarity": "Uncommon", "type": "Food", "bonus": "+energy", "score": 2},
    "ember_meat": {"name": "Ember Meat", "rarity": "Rare", "type": "Food", "bonus": "+strength training", "score": 4},
    # Materials
    "shiny_scale": {"name": "Shiny Scale", "rarity": "Common", "type": "Material", "bonus": "crafting", "score": 1},
    "ancient_coin": {"name": "Ancient Coin", "rarity": "Uncommon", "type": "Treasure", "bonus": "+tokens", "score": 2},
    "crystal_shard": {"name": "Crystal Shard", "rarity": "Rare", "type": "Material", "bonus": "research", "score": 4},
    "storm_feather": {"name": "Storm Feather", "rarity": "Rare", "type": "Relic", "bonus": "+agility", "score": 5},
    "fire_heart": {"name": "Fire Heart", "rarity": "Epic", "type": "Relic", "bonus": "+strength", "score": 8},
    "void_gem": {"name": "Void Gem", "rarity": "Mythic", "type": "Relic", "bonus": "+all stats", "score": 18},
    "frost_pearl": {"name": "Frost Pearl", "rarity": "Epic", "type": "Relic", "bonus": "+defense", "score": 8},
    "sunstone": {"name": "Sunstone", "rarity": "Legendary", "type": "Relic", "bonus": "+health", "score": 13},
    # Equipment
    "training_collar": {"name": "Training Collar", "rarity": "Uncommon", "type": "Equipment", "slot": "Collar", "bonus": "+2 Strength", "stats": {"strength": 2}, "score": 3},
    "forest_cloak": {"name": "Forest Cloak", "rarity": "Rare", "type": "Equipment", "slot": "Armor", "bonus": "+2 Defense +1 Luck", "stats": {"defense": 2, "luck": 1}, "score": 5},
    "storm_wings": {"name": "Storm Wings", "rarity": "Epic", "type": "Equipment", "slot": "Wings", "bonus": "+4 Agility", "stats": {"agility": 4}, "score": 8},
    "scholar_charm": {"name": "Scholar Charm", "rarity": "Rare", "type": "Equipment", "slot": "Trinket", "bonus": "+3 Intelligence", "stats": {"intelligence": 3}, "score": 5},
    "dragon_crown": {"name": "Dragon Crown", "rarity": "Legendary", "type": "Equipment", "slot": "Crown", "bonus": "+4 Luck +2 Bond Power", "stats": {"luck": 4, "bond_power": 2}, "score": 12},
    "void_artifact": {"name": "Void Artifact", "rarity": "Mythic", "type": "Equipment", "slot": "Artifact", "bonus": "+3 all combat stats", "stats": {"strength": 3, "defense": 3, "agility": 3, "intelligence": 3, "luck": 3}, "score": 18},
}

DEFAULT_QUESTS = {
    "care_daily": {"title": "Daily Care", "description": "Care for the dragon 5 times.", "target": 5, "reward_text": "50 Guild Tokens + 25 XP"},
    "adventure_daily": {"title": "Explorer", "description": "Complete 2 adventures.", "target": 2, "reward_text": "100 Guild Tokens + Rare loot"},
    "combat_daily": {"title": "Battle Ready", "description": "Win 3 adventure encounters.", "target": 3, "reward_text": "150 Guild Tokens + equipment roll"},
    "collector_weekly": {"title": "Hoard Builder", "description": "Collect 15 loot items.", "target": 15, "reward_text": "250 Guild Tokens + Epic loot chance"},
    "bond_story": {"title": "Trusted Keeper", "description": "Raise the dragon bond to 100.", "target": 100, "reward_text": "Title progress + memory"},
}

LAIR_UPGRADES = {
    "nest": {"name": "Cozy Nest", "emoji": "🪺", "max": 5, "base_cost": 120, "bonus": "+rest recovery and health"},
    "garden": {"name": "Moon Berry Garden", "emoji": "🌿", "max": 5, "base_cost": 160, "bonus": "+food and happiness"},
    "training": {"name": "Training Grounds", "emoji": "🏋️", "max": 5, "base_cost": 220, "bonus": "+strength and XP"},
    "library": {"name": "Dragon Library", "emoji": "📚", "max": 5, "base_cost": 260, "bonus": "+intelligence and quest progress"},
    "forge": {"name": "Tiny Forge", "emoji": "⚒️", "max": 5, "base_cost": 320, "bonus": "+equipment power"},
    "treasury": {"name": "Treasure Room", "emoji": "🏦", "max": 5, "base_cost": 300, "bonus": "+tokens and luck"},
}

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def ensure_rpg_tables(guild_id: int | None = None):
    def work():
        with db_session() as con:
            cur = con.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS inventory (
                guild_id INTEGER, user_id INTEGER DEFAULT 0, item_key TEXT, item_name TEXT,
                rarity TEXT DEFAULT 'Common', item_type TEXT DEFAULT 'Material', quantity INTEGER DEFAULT 0,
                first_found_at TEXT, PRIMARY KEY (guild_id, user_id, item_key)
            )""")
            cur.execute("""CREATE TABLE IF NOT EXISTS equipment (
                guild_id INTEGER, slot TEXT, item_key TEXT, item_name TEXT, rarity TEXT DEFAULT 'Common',
                bonus_text TEXT DEFAULT '', equipped_at TEXT, PRIMARY KEY (guild_id, slot)
            )""")
            cur.execute("""CREATE TABLE IF NOT EXISTS quests (
                guild_id INTEGER, quest_key TEXT, title TEXT, description TEXT, progress INTEGER DEFAULT 0,
                target INTEGER DEFAULT 1, reward_text TEXT DEFAULT '', claimed INTEGER DEFAULT 0,
                updated_at TEXT, PRIMARY KEY (guild_id, quest_key)
            )""")
            cur.execute("""CREATE TABLE IF NOT EXISTS lair_upgrades (
                guild_id INTEGER, upgrade_key TEXT, level INTEGER DEFAULT 0, updated_at TEXT,
                PRIMARY KEY (guild_id, upgrade_key)
            )""")
            cur.execute("""CREATE TABLE IF NOT EXISTS adventure_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, user_id INTEGER,
                area_key TEXT, result TEXT, reward_text TEXT, created_at TEXT
            )""")
    execute_with_retry(work)
    if guild_id is not None:
        ensure_default_quests(guild_id)

def ensure_default_quests(guild_id: int):
    ensure_rpg_tables()
    def work():
        with db_session() as con:
            cur = con.cursor()
            for key, q in DEFAULT_QUESTS.items():
                cur.execute("""INSERT OR IGNORE INTO quests
                    (guild_id, quest_key, title, description, target, reward_text, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (guild_id, key, q["title"], q["description"], q["target"], q["reward_text"], now_iso()))
    return execute_with_retry(work)

def add_inventory_item(guild_id: int, item_key: str, quantity: int = 1, user_id: int = 0):
    ensure_rpg_tables(guild_id)
    item = ITEMS.get(item_key, {"name": item_key.replace("_", " ").title(), "rarity": "Common", "type": "Material", "bonus": "", "score": 1})
    def work():
        with db_session() as con:
            cur = con.cursor()
            cur.execute("""INSERT INTO inventory
                (guild_id, user_id, item_key, item_name, rarity, item_type, quantity, first_found_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(guild_id, user_id, item_key)
                DO UPDATE SET quantity = quantity + excluded.quantity""",
                (guild_id, user_id, item_key, item["name"], item["rarity"], item["type"], quantity, now_iso()))
    execute_with_retry(work)
    progress_quest(guild_id, "collector_weekly", quantity)
    return item

def get_inventory(guild_id: int, user_id: int = 0, limit: int = 50):
    ensure_rpg_tables(guild_id)
    with db_session(row_factory=True) as con:
        cur = con.cursor()
        cur.execute("""SELECT item_key,item_name,rarity,item_type,quantity
            FROM inventory WHERE guild_id=? AND user_id=? AND quantity>0
            ORDER BY item_type ASC, quantity DESC, item_name ASC LIMIT ?""", (guild_id, user_id, limit))
        return cur.fetchall()

def progress_quest(guild_id: int, quest_key: str, amount: int = 1):
    ensure_default_quests(guild_id)
    def work():
        with db_session() as con:
            con.cursor().execute("""UPDATE quests SET progress=MIN(target,progress+?), updated_at=?
                WHERE guild_id=? AND quest_key=? AND claimed=0""", (amount, now_iso(), guild_id, quest_key))
    return execute_with_retry(work)

def set_quest_progress(guild_id: int, quest_key: str, value: int):
    ensure_default_quests(guild_id)
    def work():
        with db_session() as con:
            con.cursor().execute("""UPDATE quests SET progress=MIN(target,MAX(progress,?)), updated_at=?
                WHERE guild_id=? AND quest_key=? AND claimed=0""", (value, now_iso(), guild_id, quest_key))
    return execute_with_retry(work)

def get_quests(guild_id: int):
    ensure_default_quests(guild_id)
    with db_session(row_factory=True) as con:
        cur = con.cursor()
        cur.execute("""SELECT quest_key,title,description,progress,target,reward_text,claimed
            FROM quests WHERE guild_id=? ORDER BY claimed ASC, quest_key ASC""", (guild_id,))
        return cur.fetchall()

def claim_completed_quests(guild_id: int):
    ensure_default_quests(guild_id)
    rewards = []
    def work():
        nonlocal rewards
        with db_session(row_factory=True) as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM quests WHERE guild_id=? AND claimed=0 AND progress>=target", (guild_id,))
            rows = cur.fetchall()
            for row in rows:
                tokens = 50
                xp = 25
                loot = None
                if row["quest_key"] == "adventure_daily":
                    tokens = 100; xp = 75; loot = "crystal_shard"
                elif row["quest_key"] == "combat_daily":
                    tokens = 150; xp = 100; loot = random.choice(["training_collar", "forest_cloak", "scholar_charm"])
                elif row["quest_key"] == "collector_weekly":
                    tokens = 250; xp = 150; loot = random.choice(["fire_heart", "storm_wings", "frost_pearl"])
                elif row["quest_key"] == "bond_story":
                    tokens = 200; xp = 200; loot = "dragon_crown"
                cur.execute("UPDATE dragon SET guild_tokens=guild_tokens+?, lifetime_guild_tokens=lifetime_guild_tokens+?, xp=xp+? WHERE guild_id=?",
                            (tokens, tokens, xp, guild_id))
                if loot:
                    item = ITEMS[loot]
                    cur.execute("""INSERT INTO inventory (guild_id, user_id, item_key, item_name, rarity, item_type, quantity, first_found_at)
                        VALUES (?,0,?,?,?,?,1,?) ON CONFLICT(guild_id,user_id,item_key)
                        DO UPDATE SET quantity=quantity+1""", (guild_id, loot, item["name"], item["rarity"], item["type"], now_iso()))
                cur.execute("UPDATE quests SET claimed=1, updated_at=? WHERE guild_id=? AND quest_key=?", (now_iso(), guild_id, row["quest_key"]))
                rewards.append(f"✅ **{row['title']}** — +{tokens} tokens, +{xp} XP" + (f", +{ITEMS[loot]['name']}" if loot else ""))
    execute_with_retry(work)
    return rewards

def get_equipment(guild_id: int):
    ensure_rpg_tables(guild_id)
    with db_session(row_factory=True) as con:
        cur = con.cursor()
        cur.execute("SELECT slot,item_key,item_name,rarity,bonus_text FROM equipment WHERE guild_id=? ORDER BY slot", (guild_id,))
        return cur.fetchall()

def equip_item(guild_id: int, item_key: str):
    ensure_rpg_tables(guild_id)
    item = ITEMS.get(item_key)
    if not item or item.get("type") != "Equipment":
        return False, "That item is not equipment."
    slot = item.get("slot", "Artifact")
    def work():
        with db_session() as con:
            cur = con.cursor()
            cur.execute("SELECT quantity FROM inventory WHERE guild_id=? AND user_id=0 AND item_key=?", (guild_id, item_key))
            row = cur.fetchone()
            if not row or row[0] <= 0:
                return False, f"The guild does not have **{item['name']}**."
            cur.execute("""INSERT OR REPLACE INTO equipment
                (guild_id, slot, item_key, item_name, rarity, bonus_text, equipped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""", (guild_id, slot, item_key, item["name"], item["rarity"], item["bonus"], now_iso()))
            return True, f"Equipped **{item['name']}** in slot **{slot}**."
    return execute_with_retry(work)

def equip_best_items(guild_id: int):
    ensure_rpg_tables(guild_id)
    equipped = []
    with db_session(row_factory=True) as con:
        cur = con.cursor()
        cur.execute("SELECT item_key, quantity FROM inventory WHERE guild_id=? AND user_id=0 AND quantity>0", (guild_id,))
        rows = cur.fetchall()
    best_by_slot = {}
    for row in rows:
        item = ITEMS.get(row["item_key"])
        if not item or item.get("type") != "Equipment":
            continue
        slot = item.get("slot", "Artifact")
        if slot not in best_by_slot or item.get("score", 0) > ITEMS[best_by_slot[slot]].get("score", 0):
            best_by_slot[slot] = row["item_key"]
    for key in best_by_slot.values():
        ok, msg = equip_item(guild_id, key)
        if ok:
            equipped.append(msg)
    return equipped

def equipment_stat_bonus(guild_id: int):
    bonus = {"health": 0, "strength": 0, "defense": 0, "agility": 0, "intelligence": 0, "luck": 0, "bond_power": 0}
    for eq in get_equipment(guild_id):
        item = ITEMS.get(eq["item_key"], {})
        for k, v in item.get("stats", {}).items():
            bonus[k] = bonus.get(k, 0) + v
    forge = get_lair_level(guild_id, "forge")
    if forge:
        bonus["strength"] += forge
        bonus["defense"] += forge
    return bonus

def get_lair_level(guild_id: int, upgrade_key: str):
    ensure_rpg_tables(guild_id)
    with db_session(row_factory=True) as con:
        cur = con.cursor()
        cur.execute("SELECT level FROM lair_upgrades WHERE guild_id=? AND upgrade_key=?", (guild_id, upgrade_key))
        row = cur.fetchone()
        return int(row["level"]) if row else 0

def get_lair_upgrades(guild_id: int):
    ensure_rpg_tables(guild_id)
    levels = {k: 0 for k in LAIR_UPGRADES}
    with db_session(row_factory=True) as con:
        cur = con.cursor()
        cur.execute("SELECT upgrade_key, level FROM lair_upgrades WHERE guild_id=?", (guild_id,))
        for row in cur.fetchall():
            levels[row["upgrade_key"]] = row["level"]
    return levels

def lair_upgrade_cost(key: str, level: int):
    data = LAIR_UPGRADES[key]
    return data["base_cost"] * (level + 1)

def upgrade_lair(guild_id: int, upgrade_key: str):
    ensure_rpg_tables(guild_id)
    if upgrade_key not in LAIR_UPGRADES:
        return False, "Unknown lair upgrade."
    data = LAIR_UPGRADES[upgrade_key]
    level = get_lair_level(guild_id, upgrade_key)
    if level >= data["max"]:
        return False, f"{data['name']} is already max level."
    cost = lair_upgrade_cost(upgrade_key, level)
    def work():
        with db_session() as con:
            cur = con.cursor()
            cur.execute("SELECT guild_tokens FROM dragon WHERE guild_id=?", (guild_id,))
            row = cur.fetchone()
            if not row or row[0] < cost:
                return False, f"Need **{cost} Guild Tokens** to upgrade {data['name']}."
            cur.execute("UPDATE dragon SET guild_tokens=guild_tokens-? WHERE guild_id=?", (cost, guild_id))
            cur.execute("""INSERT INTO lair_upgrades (guild_id, upgrade_key, level, updated_at)
                VALUES (?, ?, 1, ?) ON CONFLICT(guild_id, upgrade_key)
                DO UPDATE SET level=level+1, updated_at=excluded.updated_at""", (guild_id, upgrade_key, now_iso()))
            return True, f"{data['emoji']} Upgraded **{data['name']}** to level **{level+1}**."
    return execute_with_retry(work)

def compute_dragon_stats(guild_id: int):
    d = get_dragon(guild_id)
    stage, _ = get_stage(d["xp"])
    stage_bonus = {"Egg": 0, "Hatchling": 2, "Young Dragon": 6, "Adult Dragon": 12, "Ancient Dragon": 20, "Elder Dragon": 30}.get(stage, 0)
    lair = get_lair_upgrades(guild_id)
    eq = equipment_stat_bonus(guild_id)
    stats = {
        "health": min(250, 70 + d["bond"] // 3 + stage_bonus * 3 + lair.get("nest", 0) * 8 + eq.get("health", 0)),
        "strength": 5 + stage_bonus + d["xp"] // 110000 + lair.get("training", 0) * 2 + eq.get("strength", 0),
        "defense": 5 + stage_bonus + d["cleanliness"] // 12 + lair.get("forge", 0) + eq.get("defense", 0),
        "agility": 5 + stage_bonus + d["energy"] // 12 + eq.get("agility", 0),
        "intelligence": 5 + d["research_points"] // 20 + lair.get("library", 0) * 2 + eq.get("intelligence", 0),
        "luck": 5 + d["happiness"] // 12 + lair.get("treasury", 0) * 2 + eq.get("luck", 0),
        "bond_power": d["bond"] // 20 + eq.get("bond_power", 0),
    }
    return stats

def simulate_combat(guild_id: int, monster: dict, boss: bool = False):
    stats = compute_dragon_stats(guild_id)
    dragon_hp = stats["health"]
    mon_hp = monster["hp"] * (2 if boss else 1)
    mon_attack = monster["attack"] + (monster["attack"] // 2 if boss else 0)
    mon_def = monster["defense"] + (monster["defense"] // 2 if boss else 0)
    rounds = []
    for turn in range(1, 6):
        crit = random.random() < min(0.35, 0.05 + stats["luck"] / 250)
        dodge = random.random() < min(0.30, stats["agility"] / 220)
        dmg = max(1, stats["strength"] + random.randint(0, max(2, stats["intelligence"] // 3)) - mon_def)
        if crit:
            dmg = int(dmg * 1.7)
        mon_hp -= dmg
        rounds.append(f"Turn {turn}: Dragon hits for **{dmg}**" + (" CRIT" if crit else "") + ".")
        if mon_hp <= 0:
            return True, dragon_hp, rounds
        if dodge:
            rounds.append(f"Turn {turn}: Dragon dodged the counterattack.")
            continue
        incoming = max(1, mon_attack + random.randint(0, 4) - stats["defense"])
        dragon_hp -= incoming
        rounds.append(f"Turn {turn}: {monster['name']} deals **{incoming}** damage.")
        if dragon_hp <= 0:
            return False, 0, rounds
    return mon_hp <= dragon_hp, max(1, dragon_hp), rounds
