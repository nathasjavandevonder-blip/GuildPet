from datetime import datetime, timezone
from database import db_session, execute_with_retry

RARITY_EMOJI = {"Common":"⚪","Uncommon":"🟢","Rare":"🔵","Epic":"🟣","Legendary":"🟠","Mythic":"🔴"}
ITEMS = {
    "moon_berry": {"name":"Moon Berry","rarity":"Common","type":"Food","bonus":"+hunger"},
    "shiny_scale": {"name":"Shiny Scale","rarity":"Common","type":"Material","bonus":"crafting"},
    "ancient_coin": {"name":"Ancient Coin","rarity":"Uncommon","type":"Treasure","bonus":"+tokens"},
    "crystal_shard": {"name":"Crystal Shard","rarity":"Rare","type":"Material","bonus":"research"},
    "storm_feather": {"name":"Storm Feather","rarity":"Rare","type":"Relic","bonus":"+agility"},
    "fire_heart": {"name":"Fire Heart","rarity":"Epic","type":"Relic","bonus":"+strength"},
    "dragon_crown": {"name":"Dragon Crown","rarity":"Legendary","type":"Equipment","bonus":"+luck +bond"},
    "void_gem": {"name":"Void Gem","rarity":"Mythic","type":"Relic","bonus":"+all stats"},
}
DEFAULT_QUESTS = {
    "care_daily": {"title":"Daily Care","description":"Care for the dragon 5 times.","target":5,"reward_text":"50 Guild Tokens + 25 XP"},
    "adventure_daily": {"title":"Explorer","description":"Complete 2 adventures.","target":2,"reward_text":"100 Guild Tokens + 1 Rare loot roll"},
    "bond_story": {"title":"Trusted Keeper","description":"Raise the dragon bond to 100.","target":100,"reward_text":"Title progress + memory"},
}
def now_iso(): return datetime.now(timezone.utc).isoformat()
def ensure_default_quests(guild_id:int):
    def work():
        with db_session() as con:
            cur=con.cursor()
            for key,q in DEFAULT_QUESTS.items():
                cur.execute("""INSERT OR IGNORE INTO quests (guild_id, quest_key, title, description, target, reward_text, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)""", (guild_id,key,q["title"],q["description"],q["target"],q["reward_text"],now_iso()))
    return execute_with_retry(work)
def add_inventory_item(guild_id:int,item_key:str,quantity:int=1,user_id:int=0):
    item=ITEMS.get(item_key,{"name":item_key.replace("_"," ").title(),"rarity":"Common","type":"Material","bonus":""})
    def work():
        with db_session() as con:
            cur=con.cursor()
            cur.execute("""INSERT INTO inventory (guild_id, user_id, item_key, item_name, rarity, item_type, quantity, first_found_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(guild_id, user_id, item_key) DO UPDATE SET quantity = quantity + excluded.quantity""", (guild_id,user_id,item_key,item["name"],item["rarity"],item["type"],quantity,now_iso()))
    execute_with_retry(work); return item
def get_inventory(guild_id:int,user_id:int=0,limit:int=25):
    ensure_default_quests(guild_id)
    with db_session(row_factory=True) as con:
        cur=con.cursor(); cur.execute("""SELECT item_key,item_name,rarity,item_type,quantity FROM inventory WHERE guild_id=? AND user_id=? AND quantity>0 ORDER BY quantity DESC, item_name ASC LIMIT ?""",(guild_id,user_id,limit)); return cur.fetchall()
def progress_quest(guild_id:int,quest_key:str,amount:int=1):
    ensure_default_quests(guild_id)
    def work():
        with db_session() as con:
            con.cursor().execute("""UPDATE quests SET progress=MIN(target,progress+?), updated_at=? WHERE guild_id=? AND quest_key=? AND claimed=0""",(amount,now_iso(),guild_id,quest_key))
    return execute_with_retry(work)
def set_quest_progress(guild_id:int,quest_key:str,value:int):
    ensure_default_quests(guild_id)
    def work():
        with db_session() as con:
            con.cursor().execute("""UPDATE quests SET progress=MIN(target,MAX(progress,?)), updated_at=? WHERE guild_id=? AND quest_key=? AND claimed=0""",(value,now_iso(),guild_id,quest_key))
    return execute_with_retry(work)
def get_quests(guild_id:int):
    ensure_default_quests(guild_id)
    with db_session(row_factory=True) as con:
        cur=con.cursor(); cur.execute("""SELECT quest_key,title,description,progress,target,reward_text,claimed FROM quests WHERE guild_id=? ORDER BY claimed ASC, quest_key ASC""",(guild_id,)); return cur.fetchall()
def get_equipment(guild_id:int):
    with db_session(row_factory=True) as con:
        cur=con.cursor(); cur.execute("SELECT slot,item_name,rarity,bonus_text FROM equipment WHERE guild_id=? ORDER BY slot",(guild_id,)); return cur.fetchall()
