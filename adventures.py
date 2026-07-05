import random
from datetime import datetime, timezone, timedelta
import discord
from database import db_session, execute_with_retry, get_dragon, add_memory_tx
from progression import has_research, add_guild_level_xp
from utils import get_stage
from rpg import add_inventory_item, progress_quest, set_quest_progress, ITEMS, RARITY_EMOJI

ADVENTURES={
 "forest":{"name":"Ancient Forest","emoji":"🌲","minutes":10,"min_xp":0,"energy_cost":8,"reward_tokens":(35,90),"reward_xp":(15,45),"loot":["moon_berry","shiny_scale","ancient_coin"],"monsters":["Wild Boar","Vine Sprite","Forest Imp"],"description":"A safe route with berries, butterflies and small treasures."},
 "lake":{"name":"Crystal Lake","emoji":"🌊","minutes":20,"min_xp":250*55,"energy_cost":10,"reward_tokens":(70,150),"reward_xp":(30,80),"loot":["moon_berry","crystal_shard","ancient_coin"],"monsters":["Lake Serpent","Crystal Crab","Mist Wisp"],"description":"A calm lake where crystals sometimes wash onto the shore."},
 "ruins":{"name":"Ancient Ruins","emoji":"🏛️","minutes":30,"min_xp":750*55,"energy_cost":12,"reward_tokens":(110,240),"reward_xp":(60,130),"loot":["ancient_coin","crystal_shard","storm_feather"],"monsters":["Stone Guardian","Dust Wraith","Relic Spider"],"description":"Old ruins with hidden rooms, dusty relics and risky discoveries."},
 "mountains":{"name":"Storm Mountains","emoji":"⛰️","minutes":45,"min_xp":1500*55,"energy_cost":15,"reward_tokens":(180,360),"reward_xp":(90,210),"loot":["storm_feather","crystal_shard","dragon_crown"],"monsters":["Thunder Roc","Mountain Troll","Storm Drake"],"description":"A dangerous mountain path with strong winds and rare minerals."},
 "volcano":{"name":"Fire Volcano","emoji":"🌋","minutes":60,"min_xp":3000*55,"energy_cost":18,"reward_tokens":(280,520),"reward_xp":(160,320),"loot":["fire_heart","crystal_shard","dragon_crown"],"monsters":["Lava Hound","Ash Golem","Fire Wyvern"],"description":"A hot volcanic route for stronger dragons. High risk, high reward."},
 "void":{"name":"Void Gate","emoji":"🌌","minutes":90,"min_xp":6000*55,"energy_cost":22,"reward_tokens":(420,850),"reward_xp":(250,520),"loot":["void_gem","dragon_crown","fire_heart"],"monsters":["Voidling","Star Eater","Ancient Shadow"],"description":"A strange realm with legendary discoveries."},
}
DISCOVERIES=["found a glowing feather","chased a strange butterfly","dug up an old coin","found claw marks from another dragon","heard a mysterious song in the distance","brought home a shiny stone","met a tiny forest spirit","found old guild markings carved into stone"]
FAIL_LINES=["came back tired and empty-clawed","got scared by strange noises and returned early","lost the trail and came home confused","spent the whole adventure chasing its own tail"]
def _now(): return datetime.now(timezone.utc)
def _parse(value): return datetime.fromisoformat(value)
def active_adventure(guild_id:int):
    with db_session(row_factory=True) as con:
        cur=con.cursor(); cur.execute("SELECT * FROM adventures WHERE guild_id=? AND claimed=0",(guild_id,)); return cur.fetchone()
def available_adventures(guild_id:int):
    d=get_dragon(guild_id); return [(k,a) for k,a in ADVENTURES.items() if d["xp"]>=a["min_xp"]]
def start_adventure(guild_id:int,user_id:int,area_key:str):
    def work():
        if area_key not in ADVENTURES: return False,"Unknown adventure."
        d=get_dragon(guild_id); adv=ADVENTURES[area_key]
        if d["xp"]<adv["min_xp"]: return False,f"This adventure requires **{adv['min_xp']} dragon XP**."
        if d["energy"]<adv["energy_cost"]: return False,f"⚡ The dragon needs at least **{adv['energy_cost']} energy** for this adventure. Let it rest first."
        existing=active_adventure(guild_id)
        if existing:
            mins=max(1,int((_parse(existing["returns_at"])-_now()).total_seconds()//60)); return False,f"🐉 The dragon is already on an adventure and returns in about **{mins} minutes**."
        minutes=adv["minutes"]
        if has_research(guild_id,"dragon_library"): minutes=max(5,int(minutes*0.85))
        returns_at=_now()+timedelta(minutes=minutes)
        with db_session() as con:
            cur=con.cursor()
            cur.execute("""INSERT OR REPLACE INTO adventures (guild_id,user_id,area_key,started_at,returns_at,claimed) VALUES (?,?,?,?,?,0)""",(guild_id,user_id,area_key,_now().isoformat(),returns_at.isoformat()))
            cur.execute("""UPDATE dragon SET pose=?, energy=max(0,energy-?), dragon_message=?, last_action_text=? WHERE guild_id=?""",("adventuring",adv["energy_cost"],f"I am exploring the {adv['name']}!",f"{adv['emoji']} The dragon left for **{adv['name']}** and will return soon.",guild_id))
            add_memory_tx(cur,guild_id,f"The dragon left for an adventure in {adv['name']}.")
        return True,f"{adv['emoji']} Adventure started: **{adv['name']}**. The dragon returns in about **{minutes} minutes**."
    return execute_with_retry(work)
def _loot_roll(adv):
    key=random.choice(adv["loot"]); item=ITEMS.get(key,{"name":key,"rarity":"Common","type":"Material"}); qty=1 if item["rarity"] not in ["Common","Uncommon"] else random.randint(1,3); return key,item,qty
def claim_adventure(guild_id:int,user):
    def work():
        adventure=active_adventure(guild_id)
        if not adventure: return False,"There is no active adventure to claim."
        returns_at=_parse(adventure["returns_at"])
        if _now()<returns_at:
            mins=max(1,int((returns_at-_now()).total_seconds()//60)); return False,f"⏳ The dragon is still adventuring. Return in about **{mins} minutes**."
        adv=ADVENTURES[adventure["area_key"]]; d=get_dragon(guild_id); stage,_=get_stage(d["xp"])
        strength={"Egg":0,"Hatchling":2,"Young Dragon":5,"Adult Dragon":9,"Ancient Dragon":14,"Elder Dragon":20}.get(stage,0)
        fail_chance=max(0.05,0.18-(d["bond"]/1000)-(strength/300)); monster=random.choice(adv["monsters"]); boss=random.random()<0.08; failed=random.random()<fail_chance
        if failed:
            tokens=0; xp=random.randint(8,25); message=f"The dragon met **{monster}**, got overwhelmed, and {random.choice(FAIL_LINES)}."; loot_text="No loot found."
        else:
            tokens=random.randint(*adv["reward_tokens"]); xp=random.randint(*adv["reward_xp"])
            if boss: tokens=int(tokens*1.75); xp=int(xp*1.5)
            item_key,item,qty=_loot_roll(adv); add_inventory_item(guild_id,item_key,qty,0); icon=RARITY_EMOJI.get(item["rarity"],"⚪"); loot_text=f"{icon} **{item['name']}** ×{qty} ({item['rarity']})"
            message=(f"The dragon defeated a boss **{monster}**, " if boss else f"The dragon avoided **{monster}**, ")+random.choice(DISCOVERIES)+", and brought treasure home."
        with db_session() as con:
            cur=con.cursor(); cur.execute("UPDATE adventures SET claimed=1 WHERE guild_id=?",(guild_id,))
            cur.execute("""UPDATE dragon SET guild_tokens=guild_tokens+?, lifetime_guild_tokens=lifetime_guild_tokens+?, xp=xp+?, energy=max(0,energy-5), happiness=min(100,happiness+5), pose=?, visual_event=?, dragon_message=?, last_action_text=? WHERE guild_id=?""",(tokens,tokens,xp,"celebrating" if not failed else "sad","adventure",message,f"{adv['emoji']} **{user.display_name}** welcomed the dragon back from **{adv['name']}**.",guild_id))
            cur.execute("INSERT INTO memories (guild_id,text,created_at) VALUES (?,?,?)",(guild_id,f"Adventure: {adv['name']} — {message}",_now().isoformat()))
        add_guild_level_xp(guild_id,max(1,tokens//3)+xp); progress_quest(guild_id,"adventure_daily",1); set_quest_progress(guild_id,"bond_story",d["bond"])
        return True,(f"⚠️ **Adventure complete:** {message}\nReward: **{xp} XP**, **0 Guild Tokens**.\n{loot_text}" if failed else f"🎒 **Adventure complete:** {message}\nReward: **{xp} XP** and **{tokens} Guild Tokens**.\nLoot: {loot_text}")
    return execute_with_retry(work)
def adventure_status_text(guild_id:int):
    adventure=active_adventure(guild_id)
    if not adventure: return "🐉 The dragon is not currently on an adventure."
    adv=ADVENTURES[adventure["area_key"]]; returns_at=_parse(adventure["returns_at"])
    if _now()>=returns_at: return f"{adv['emoji']} The dragon has returned from **{adv['name']}** and is waiting to be claimed."
    mins=max(1,int((returns_at-_now()).total_seconds()//60)); return f"{adv['emoji']} The dragon is exploring **{adv['name']}** and returns in about **{mins} minutes**."
def make_adventure_embed(guild_id:int):
    d=get_dragon(guild_id); status=adventure_status_text(guild_id); stage,_=get_stage(d["xp"])
    embed=discord.Embed(title="🗺️ Guild Dragon Adventures",description=f"**Stage:** {stage}\n**Energy:** {d['energy']}%\n\n{status}\n\nChoose a route below. Adventures cost energy, can find loot, and may trigger monsters or bosses.",color=0x5865F2)
    for key,adv in ADVENTURES.items():
        lock="✅" if d["xp"]>=adv["min_xp"] else "🔒"
        embed.add_field(name=f"{lock} {adv['emoji']} {adv['name']}", value=f"{adv['description']}\nTime: **{adv['minutes']}m** • Energy: **{adv['energy_cost']}** • XP req: **{adv['min_xp']}**", inline=False)
    return embed
