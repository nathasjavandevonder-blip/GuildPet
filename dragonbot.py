import os
import sqlite3
import random
import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN') or os.getenv('TOKEN')
DB_FILE = 'guild_dragon.db'

# Paste real image URLs here later. Leave empty for now.
STAGE_IMAGES = {
    'Egg': '',
    'Hatchling': '',
    'Young Dragon': '',
    'Adult Dragon': '',
    'Ancient Dragon': '',
    'Elder Dragon': '',
}

LAIR_IMAGES = {
    'Empty Cave': '',
    'Moss Nest': '',
    'Crystal Nest': '',
    'Lava Nest': '',
    'Royal Dragon Hall': '',
    'Sky Fortress': '',
}

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

SHOP = {
    'moss_nest': ('Moss Nest', 500, 'lair', 'A soft green nest for the dragon.'),
    'crystal_nest': ('Crystal Nest', 1500, 'lair', 'A magical nest filled with crystals.'),
    'lava_nest': ('Lava Nest', 1500, 'lair', 'A warm volcanic nest.'),
    'royal_hall': ('Royal Dragon Hall', 5000, 'lair', 'A royal room for a legendary dragon.'),
    'sky_fortress': ('Sky Fortress', 15000, 'lair', 'A fortress above the clouds.'),
    'golden_bowl': ('Golden Bowl', 1000, 'upgrade', 'Feed gives +5 extra hunger.'),
    'training_dummy': ('Training Dummy', 1200, 'upgrade', 'Train gives +3 extra XP.'),
    'bubble_bath': ('Bubble Bath', 1000, 'upgrade', 'Clean gives +5 extra cleanliness.'),
}

ACHIEVEMENTS = {
    'first_feed': ('🍖 First Meal', 'Feed the dragon once.'),
    'feed_25': ('🍗 Dragon Chef', 'Feed the dragon 25 times.'),
    'play_25': ('🎾 Play Champion', 'Play with the dragon 25 times.'),
    'train_25': ('🔥 Trainer', 'Train the dragon 25 times.'),
    'clean_25': ('🛁 Clean Keeper', 'Clean the dragon 25 times.'),
    'bond_25': ('❤️ Dragon Friend', 'Bond with the dragon 25 times.'),
    'points_500': ('🏅 Caretaker', 'Earn 500 points.'),
    'points_2500': ('🏆 Dragon Keeper', 'Earn 2,500 points.'),
}

def db():
    return sqlite3.connect(DB_FILE)

def init_db():
    con = db(); cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS dragon (
        guild_id INTEGER PRIMARY KEY,
        channel_id INTEGER,
        message_id INTEGER,
        event_channel_id INTEGER,
        hunger INTEGER DEFAULT 60,
        happiness INTEGER DEFAULT 60,
        energy INTEGER DEFAULT 60,
        cleanliness INTEGER DEFAULT 60,
        bond INTEGER DEFAULT 0,
        xp INTEGER DEFAULT 0,
        guild_tokens INTEGER DEFAULT 0,
        personality TEXT DEFAULT 'Curious',
        lair TEXT DEFAULT 'Empty Cave',
        pose TEXT DEFAULT 'waiting',
        last_action_text TEXT DEFAULT 'The dragon is waiting for care.',
        last_decay TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS players (
        guild_id INTEGER,
        user_id INTEGER,
        tokens INTEGER DEFAULT 0,
        points INTEGER DEFAULT 0,
        feeds INTEGER DEFAULT 0,
        plays INTEGER DEFAULT 0,
        trains INTEGER DEFAULT 0,
        cleans INTEGER DEFAULT 0,
        rests INTEGER DEFAULT 0,
        bonds INTEGER DEFAULT 0,
        events INTEGER DEFAULT 0,
        PRIMARY KEY (guild_id, user_id)
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS cooldowns (
        guild_id INTEGER,
        user_id INTEGER,
        action TEXT,
        last_used TEXT,
        PRIMARY KEY (guild_id, user_id, action)
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS shop_items (
        guild_id INTEGER,
        item_key TEXT,
        bought INTEGER DEFAULT 0,
        PRIMARY KEY (guild_id, item_key)
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS achievements (
        guild_id INTEGER,
        user_id INTEGER,
        achievement_key TEXT,
        unlocked_at TEXT,
        PRIMARY KEY (guild_id, user_id, achievement_key)
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER,
        text TEXT,
        created_at TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS events (
        guild_id INTEGER PRIMARY KEY,
        event_type TEXT,
        expires_at TEXT,
        claimed_by INTEGER,
        message_id INTEGER
    )''')
    con.commit(); con.close()

def ensure_dragon(guild_id:int):
    con=db(); cur=con.cursor()
    cur.execute('INSERT OR IGNORE INTO dragon (guild_id,last_decay) VALUES (?,?)', (guild_id, datetime.now(timezone.utc).isoformat()))
    con.commit(); con.close()

def get_dragon(guild_id:int):
    ensure_dragon(guild_id)
    con=db(); con.row_factory=sqlite3.Row; cur=con.cursor()
    cur.execute('SELECT * FROM dragon WHERE guild_id=?', (guild_id,))
    row=cur.fetchone(); con.close(); return row

def clamp(v, lo=0, hi=100): return max(lo, min(hi, v))

def get_stage(xp:int):
    if xp >= 100000: return 'Elder Dragon', '🌌'
    if xp >= 40000: return 'Ancient Dragon', '👑'
    if xp >= 15000: return 'Adult Dragon', '🔥'
    if xp >= 5000: return 'Young Dragon', '🐉'
    if xp >= 1000: return 'Hatchling', '🐲'
    return 'Egg', '🥚'

def next_stage_info(xp:int):
    levels=[('Egg',0),('Hatchling',1000),('Young Dragon',5000),('Adult Dragon',15000),('Ancient Dragon',40000),('Elder Dragon',100000)]
    cur_name, cur_xp = levels[0]
    next_name, next_xp = levels[1]
    for i,(name,needed) in enumerate(levels):
        if xp >= needed:
            cur_name, cur_xp = name, needed
            if i+1 < len(levels): next_name, next_xp = levels[i+1]
            else: next_name, next_xp = 'MAX', needed
    if next_name == 'MAX': return 100, cur_xp, next_xp, next_name
    return clamp(int(((xp-cur_xp)/(next_xp-cur_xp))*100)), cur_xp, next_xp, next_name

def bar(value:int, blocks:int=10):
    filled=round((value/100)*blocks)
    return '█'*filled + '░'*(blocks-filled) + f' {value}%'

def add_memory(guild_id:int, text:str):
    con=db(); cur=con.cursor()
    cur.execute('INSERT INTO memories (guild_id,text,created_at) VALUES (?,?,?)', (guild_id,text,datetime.now(timezone.utc).isoformat()))
    con.commit(); con.close()

def has_item(guild_id:int, item_key:str):
    con=db(); cur=con.cursor(); cur.execute('SELECT bought FROM shop_items WHERE guild_id=? AND item_key=?', (guild_id,item_key))
    row=cur.fetchone(); con.close(); return bool(row and row[0])

def buy_item(guild_id:int, item_key:str):
    name,cost,kind,desc = SHOP[item_key]
    d=get_dragon(guild_id)
    if has_item(guild_id,item_key): return False, 'Already bought.'
    if d['guild_tokens'] < cost: return False, f'Need {cost} Guild Tokens. Current: {d["guild_tokens"]}.'
    con=db(); cur=con.cursor()
    cur.execute('UPDATE dragon SET guild_tokens=guild_tokens-? WHERE guild_id=?', (cost,guild_id))
    cur.execute('INSERT OR REPLACE INTO shop_items (guild_id,item_key,bought) VALUES (?,?,1)', (guild_id,item_key))
    if kind == 'lair':
        cur.execute('UPDATE dragon SET lair=?, last_action_text=? WHERE guild_id=?', (name, f'🏡 The guild unlocked **{name}**!', guild_id))
        add_memory(guild_id, f'The guild unlocked the lair upgrade: {name}.')
    con.commit(); con.close(); return True, f'✅ Bought {name}.'

def make_embed(guild_id:int):
    d=get_dragon(guild_id); stage,emoji=get_stage(d['xp']); progress,_,next_xp,next_name=next_stage_info(d['xp'])
    embed=discord.Embed(title=f'{emoji} Guild Dragon', description=(
        f'**Stage:** {stage}\n**Lair:** {d["lair"]}\n**Personality:** {d["personality"]}\n'
        f'**Guild XP:** {d["xp"]} / {next_xp}\n**Next stage:** {next_name}\n**Growth:** {bar(progress)}'
    ), color=0x7B2CFF)
    embed.add_field(name='🍖 Hunger', value=bar(d['hunger']), inline=False)
    embed.add_field(name='😊 Happiness', value=bar(d['happiness']), inline=False)
    embed.add_field(name='⚡ Energy', value=bar(d['energy']), inline=False)
    embed.add_field(name='💧 Cleanliness', value=bar(d['cleanliness']), inline=False)
    embed.add_field(name='❤️ Bond', value=bar(d['bond']), inline=False)
    embed.add_field(name='🪙 Guild Tokens', value=str(d['guild_tokens']), inline=True)
    embed.add_field(name='🎭 Pose', value=d['pose'], inline=True)
    embed.add_field(name='Last action', value=d['last_action_text'], inline=False)
    image_url = LAIR_IMAGES.get(d['lair']) or STAGE_IMAGES.get(stage)
    if image_url: embed.set_image(url=image_url)
    embed.set_footer(text='Buttons edit this one message to avoid spam.')
    return embed

def make_shop_embed(guild_id:int):
    d=get_dragon(guild_id)
    embed=discord.Embed(title='🛒 Guild Dragon Shop', description=f'Guild Tokens: **{d["guild_tokens"]}**', color=0xE2B714)
    for key,(name,cost,kind,desc) in SHOP.items():
        status='✅ Bought' if has_item(guild_id,key) else f'Cost: {cost}'
        embed.add_field(name=f'{name} — {status}', value=desc, inline=False)
    return embed

async def update_dragon_message(guild:discord.Guild):
    d=get_dragon(guild.id)
    if not d['channel_id'] or not d['message_id']: return
    channel=guild.get_channel(d['channel_id'])
    if not channel: return
    try:
        msg=await channel.fetch_message(d['message_id'])
        await msg.edit(embed=make_embed(guild.id), view=DragonView())
    except Exception:
        pass

def check_cooldown(guild_id:int, user_id:int, action:str, minutes:int=30):
    con=db(); cur=con.cursor(); now=datetime.now(timezone.utc)
    cur.execute('SELECT last_used FROM cooldowns WHERE guild_id=? AND user_id=? AND action=?', (guild_id,user_id,action))
    row=cur.fetchone()
    if row:
        last=datetime.fromisoformat(row[0]); remaining=timedelta(minutes=minutes)-(now-last)
        if remaining.total_seconds() > 0:
            con.close(); return False, int(remaining.total_seconds()//60)+1
    cur.execute('INSERT OR REPLACE INTO cooldowns (guild_id,user_id,action,last_used) VALUES (?,?,?,?)', (guild_id,user_id,action,now.isoformat()))
    con.commit(); con.close(); return True,0

def add_player_reward(guild_id:int, user_id:int, tokens:int, points:int, action:str):
    col={'feed':'feeds','play':'plays','train':'trains','clean':'cleans','rest':'rests','bond':'bonds','event':'events'}.get(action)
    con=db(); cur=con.cursor()
    cur.execute('''INSERT INTO players (guild_id,user_id,tokens,points) VALUES (?,?,?,?)
        ON CONFLICT(guild_id,user_id) DO UPDATE SET tokens=tokens+excluded.tokens, points=points+excluded.points''', (guild_id,user_id,tokens,points))
    if col: cur.execute(f'UPDATE players SET {col}={col}+1 WHERE guild_id=? AND user_id=?', (guild_id,user_id))
    con.commit(); con.close()

def update_personality(guild_id:int):
    d=get_dragon(guild_id)
    if d['bond'] >= 80 and d['happiness'] >= 80: p='Affectionate'
    elif d['energy'] >= 80 and d['bond'] >= 50: p='Playful'
    elif d['hunger'] < 25: p='Grumpy'
    elif d['cleanliness'] < 25: p='Messy'
    elif d['energy'] < 25: p='Sleepy'
    else: p='Curious'
    con=db(); cur=con.cursor(); cur.execute('UPDATE dragon SET personality=? WHERE guild_id=?', (p,guild_id)); con.commit(); con.close()

def apply_action(guild_id:int, user:discord.User, action:str):
    feed_bonus=5 if has_item(guild_id,'golden_bowl') and action=='feed' else 0
    train_bonus=3 if has_item(guild_id,'training_dummy') and action=='train' else 0
    clean_bonus=5 if has_item(guild_id,'bubble_bath') and action=='clean' else 0
    effects={
        'feed': {'hunger':10+feed_bonus,'xp':2,'tokens':8,'guild_tokens':4,'points':8,'pose':'eating','text':'fed the dragon 🍖'},
        'play': {'happiness':8,'energy':-5,'xp':2,'tokens':8,'guild_tokens':4,'points':8,'pose':'playing','text':'played with the dragon 🎾'},
        'train': {'bond':5,'energy':-10,'xp':4+train_bonus,'tokens':10,'guild_tokens':5,'points':10,'pose':'training','text':'trained the dragon 🏋️'},
        'clean': {'cleanliness':10+clean_bonus,'xp':2,'tokens':8,'guild_tokens':4,'points':8,'pose':'clean','text':'cleaned the dragon 🛁'},
        'rest': {'energy':15,'xp':1,'tokens':4,'guild_tokens':2,'points':4,'pose':'sleeping','text':'let the dragon rest 😴'},
        'bond': {'bond':8,'happiness':3,'xp':2,'tokens':8,'guild_tokens':4,'points':8,'pose':'bonding','text':'bonded with the dragon ❤️'},
    }
    e=effects[action]; d=get_dragon(guild_id); old_stage,_=get_stage(d['xp'])
    new_values={
        'hunger':clamp(d['hunger']+e.get('hunger',0)), 'happiness':clamp(d['happiness']+e.get('happiness',0)),
        'energy':clamp(d['energy']+e.get('energy',0)), 'cleanliness':clamp(d['cleanliness']+e.get('cleanliness',0)),
        'bond':clamp(d['bond']+e.get('bond',0)), 'xp':d['xp']+e['xp'], 'guild_tokens':d['guild_tokens']+e['guild_tokens']
    }
    text=f'**{user.display_name}** {e["text"]} and earned **{e["tokens"]} Dragon Tokens**.'
    new_stage,_=get_stage(new_values['xp'])
    if new_stage != old_stage:
        text += f'\n🎉 The dragon grew into **{new_stage}**!'
        add_memory(guild_id, f'The dragon grew into {new_stage}. {user.display_name} triggered the milestone.')
    con=db(); cur=con.cursor()
    cur.execute('''UPDATE dragon SET hunger=?,happiness=?,energy=?,cleanliness=?,bond=?,xp=?,guild_tokens=?,pose=?,last_action_text=? WHERE guild_id=?''',
        (new_values['hunger'],new_values['happiness'],new_values['energy'],new_values['cleanliness'],new_values['bond'],new_values['xp'],new_values['guild_tokens'],e['pose'],text,guild_id))
    con.commit(); con.close()
    add_player_reward(guild_id,user.id,e['tokens'],e['points'],action); update_personality(guild_id)

def check_achievements(guild, user_id:int):
    con=db(); con.row_factory=sqlite3.Row; cur=con.cursor(); cur.execute('SELECT * FROM players WHERE guild_id=? AND user_id=?', (guild.id,user_id)); p=cur.fetchone()
    if not p: con.close(); return []
    keys=[]
    if p['feeds'] >= 1: keys.append('first_feed')
    if p['feeds'] >= 25: keys.append('feed_25')
    if p['plays'] >= 25: keys.append('play_25')
    if p['trains'] >= 25: keys.append('train_25')
    if p['cleans'] >= 25: keys.append('clean_25')
    if p['bonds'] >= 25: keys.append('bond_25')
    if p['points'] >= 500: keys.append('points_500')
    if p['points'] >= 2500: keys.append('points_2500')
    unlocked=[]; now=datetime.now(timezone.utc).isoformat()
    for k in keys:
        cur.execute('INSERT OR IGNORE INTO achievements (guild_id,user_id,achievement_key,unlocked_at) VALUES (?,?,?,?)', (guild.id,user_id,k,now))
        if cur.rowcount: unlocked.append(k)
    con.commit(); con.close(); return unlocked

class ShopSelect(discord.ui.Select):
    def __init__(self):
        opts=[discord.SelectOption(label=v[0], value=k, description=f'{v[1]} guild tokens') for k,v in SHOP.items()]
        super().__init__(placeholder='Choose an upgrade...', options=opts)
    async def callback(self, interaction):
        ok,msg=buy_item(interaction.guild.id,self.values[0])
        await interaction.response.edit_message(content=msg, embed=make_shop_embed(interaction.guild.id), view=ShopView())
        await update_dragon_message(interaction.guild)

class ShopView(discord.ui.View):
    def __init__(self): super().__init__(timeout=120); self.add_item(ShopSelect())

class DragonView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    async def handle(self, interaction, action):
        ok,mins=check_cooldown(interaction.guild.id, interaction.user.id, action, 30)
        if not ok:
            return await interaction.response.send_message(f'⏳ You can use **{action}** again in **{mins} minutes**.', ephemeral=True)
        apply_action(interaction.guild.id, interaction.user, action)
        unlocked=check_achievements(interaction.guild, interaction.user.id)
        await interaction.response.edit_message(embed=make_embed(interaction.guild.id), view=DragonView())
        if unlocked:
            lines=[f'{ACHIEVEMENTS[k][0]} — {ACHIEVEMENTS[k][1]}' for k in unlocked]
            await interaction.followup.send('🏅 **Achievement unlocked!**\n'+'\n'.join(lines), ephemeral=True)
    @discord.ui.button(label='Feed', emoji='🍖', style=discord.ButtonStyle.danger, custom_id='dragon_feed')
    async def feed(self,i,b): await self.handle(i,'feed')
    @discord.ui.button(label='Play', emoji='🎾', style=discord.ButtonStyle.success, custom_id='dragon_play')
    async def play(self,i,b): await self.handle(i,'play')
    @discord.ui.button(label='Train', emoji='🏋️', style=discord.ButtonStyle.primary, custom_id='dragon_train')
    async def train(self,i,b): await self.handle(i,'train')
    @discord.ui.button(label='Clean', emoji='🛁', style=discord.ButtonStyle.secondary, custom_id='dragon_clean')
    async def clean(self,i,b): await self.handle(i,'clean')
    @discord.ui.button(label='Rest', emoji='😴', style=discord.ButtonStyle.secondary, custom_id='dragon_rest')
    async def rest(self,i,b): await self.handle(i,'rest')
    @discord.ui.button(label='Bond', emoji='❤️', style=discord.ButtonStyle.success, custom_id='dragon_bond')
    async def bond(self,i,b): await self.handle(i,'bond')
    @discord.ui.button(label='Shop', emoji='🛒', style=discord.ButtonStyle.primary, custom_id='dragon_shop')
    async def shop(self,i,b): await i.response.send_message(embed=make_shop_embed(i.guild.id), view=ShopView(), ephemeral=True)
    @discord.ui.button(label='Leaderboard', emoji='🏆', style=discord.ButtonStyle.primary, custom_id='dragon_leaderboard')
    async def leaderboard(self,i,b):
        con=db(); cur=con.cursor(); cur.execute('SELECT user_id,points,tokens FROM players WHERE guild_id=? ORDER BY points DESC LIMIT 10', (i.guild.id,)); rows=cur.fetchall(); con.close()
        if not rows: return await i.response.send_message('No leaderboard yet.', ephemeral=True)
        lines=[]
        for n,(uid,points,tokens) in enumerate(rows,1):
            member=i.guild.get_member(uid)
            if not member:
                try: member=await i.guild.fetch_member(uid)
                except Exception: member=None
            name=member.display_name if member else f'User {uid}'
            lines.append(f'**{n}. {name}** — {points} points | {tokens} tokens')
        await i.response.send_message('🏆 **Top Dragon Keepers**\n\n'+'\n'.join(lines), ephemeral=True)
    @discord.ui.button(label='Memories', emoji='📖', style=discord.ButtonStyle.secondary, custom_id='dragon_memories')
    async def memories(self,i,b):
        con=db(); cur=con.cursor(); cur.execute('SELECT text FROM memories WHERE guild_id=? ORDER BY id DESC LIMIT 10', (i.guild.id,)); rows=cur.fetchall(); con.close()
        if not rows: return await i.response.send_message('📖 No memories yet.', ephemeral=True)
        await i.response.send_message('📖 **Dragon Memories**\n\n'+'\n'.join('• '+r[0] for r in rows), ephemeral=True)

class EventView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label='Claim Event', emoji='🎁', style=discord.ButtonStyle.success, custom_id='dragon_event_claim')
    async def claim(self,i,b):
        con=db(); con.row_factory=sqlite3.Row; cur=con.cursor(); cur.execute('SELECT * FROM events WHERE guild_id=?', (i.guild.id,)); ev=cur.fetchone()
        if not ev: con.close(); return await i.response.send_message('This event is no longer active.', ephemeral=True)
        if ev['claimed_by']: con.close(); return await i.response.send_message('Someone already claimed this event.', ephemeral=True)
        if datetime.now(timezone.utc) > datetime.fromisoformat(ev['expires_at']): con.close(); return await i.response.send_message('This event expired.', ephemeral=True)
        tokens=random.randint(20,50); xp=random.randint(10,30)
        cur.execute('UPDATE events SET claimed_by=? WHERE guild_id=?', (i.user.id,i.guild.id))
        cur.execute('UPDATE dragon SET xp=xp+?, guild_tokens=guild_tokens+?, last_action_text=? WHERE guild_id=?', (xp,tokens,f'🎁 **{i.user.display_name}** claimed a random event reward!',i.guild.id))
        con.commit(); con.close(); add_player_reward(i.guild.id,i.user.id,tokens,tokens,'event')
        await i.response.edit_message(content=f'🎁 **{i.user.display_name}** claimed the event and won **{tokens} tokens** + **{xp} XP**!', embed=None, view=None)
        await update_dragon_message(i.guild)

@tasks.loop(minutes=30)
async def dragon_decay():
    for guild in bot.guilds:
        d=get_dragon(guild.id)
        con=db(); cur=con.cursor(); cur.execute('''UPDATE dragon SET hunger=?,happiness=?,energy=?,cleanliness=?,pose=?,last_decay=? WHERE guild_id=?''',
            (clamp(d['hunger']-3),clamp(d['happiness']-2),clamp(d['energy']-2),clamp(d['cleanliness']-2),random.choice(['waiting','sleeping','looking around','stretching','guarding the lair']),datetime.now(timezone.utc).isoformat(),guild.id))
        con.commit(); con.close(); update_personality(guild.id); await update_dragon_message(guild)

@tasks.loop(minutes=20)
async def random_events():
    for guild in bot.guilds:
        if random.random() > 0.10: continue
        d=get_dragon(guild.id); channel_id=d['event_channel_id'] or d['channel_id']
        if not channel_id: continue
        channel=guild.get_channel(channel_id)
        if not channel: continue
        title,text=random.choice([
            ('🐭 Mouse spotted!','The dragon spotted a mouse running through the lair.'),('💎 Hidden treasure!','The dragon found something shiny behind the nest.'),('🧙 Mysterious merchant!','A traveler offers a small gift to the first keeper.'),('🌧️ Storm in the lair!','The dragon needs help before the cave gets messy.'),('🥩 Rare meat appeared!','A rare piece of meat appeared near the dragon.')])
        embed=discord.Embed(title=title, description=text+'\n\nFirst person to claim gets a reward. Expires in **15 minutes**.', color=0x7B2CFF)
        msg=await channel.send(embed=embed, view=EventView())
        con=db(); cur=con.cursor(); cur.execute('INSERT OR REPLACE INTO events (guild_id,event_type,expires_at,claimed_by,message_id) VALUES (?,?,?,?,?)', (guild.id,title, (datetime.now(timezone.utc)+timedelta(minutes=15)).isoformat(), None, msg.id)); con.commit(); con.close()

@bot.tree.command(name='dragon_setup', description='Create the live Guild Dragon message in this channel.')
@app_commands.checks.has_permissions(manage_guild=True)
async def dragon_setup(interaction):
    ensure_dragon(interaction.guild.id)
    await interaction.response.send_message('Creating Guild Dragon message...', ephemeral=True)
    msg=await interaction.channel.send(embed=make_embed(interaction.guild.id), view=DragonView())
    con=db(); cur=con.cursor(); cur.execute('UPDATE dragon SET channel_id=?,message_id=?,event_channel_id=? WHERE guild_id=?', (interaction.channel.id,msg.id,interaction.channel.id,interaction.guild.id)); con.commit(); con.close()
    add_memory(interaction.guild.id, f'The Guild Dragon was born in #{interaction.channel.name}.')

@bot.tree.command(name='dragon_event_channel', description='Set this channel for random dragon events.')
@app_commands.checks.has_permissions(manage_guild=True)
async def dragon_event_channel(interaction):
    ensure_dragon(interaction.guild.id)
    con=db(); cur=con.cursor(); cur.execute('UPDATE dragon SET event_channel_id=? WHERE guild_id=?', (interaction.channel.id,interaction.guild.id)); con.commit(); con.close()
    await interaction.response.send_message('✅ Random dragon events will appear in this channel.', ephemeral=True)

@bot.tree.command(name='dragon_reset', description='Reset the Guild Dragon data. Careful!')
@app_commands.checks.has_permissions(administrator=True)
async def dragon_reset(interaction):
    con=db(); cur=con.cursor()
    for table in ['dragon','players','cooldowns','shop_items','achievements','memories','events']:
        cur.execute(f'DELETE FROM {table} WHERE guild_id=?', (interaction.guild.id,))
    con.commit(); con.close(); await interaction.response.send_message('✅ Guild Dragon data has been reset.', ephemeral=True)

@bot.event
async def on_ready():
    init_db(); bot.add_view(DragonView()); bot.add_view(EventView())
    if not dragon_decay.is_running(): dragon_decay.start()
    if not random_events.is_running(): random_events.start()
    await bot.tree.sync(); print(f'Logged in as {bot.user}')

if not TOKEN:
    raise RuntimeError('Missing DISCORD_TOKEN or TOKEN in .env file')
bot.run(TOKEN)
