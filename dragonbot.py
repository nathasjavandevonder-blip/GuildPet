import os
import sqlite3
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DB_FILE = "guild_dragon.db"

# Optional: put image URLs here later
STAGE_IMAGES = {
    "Egg": "",
    "Hatchling": "",
    "Young Dragon": "",
    "Adult Dragon": "",
    "Ancient Dragon": "",
}

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# ---------------- DATABASE ----------------

def db():
    return sqlite3.connect(DB_FILE)


def init_db():
    con = db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS dragon (
        guild_id INTEGER PRIMARY KEY,
        channel_id INTEGER,
        message_id INTEGER,
        hunger INTEGER DEFAULT 60,
        happiness INTEGER DEFAULT 60,
        energy INTEGER DEFAULT 60,
        cleanliness INTEGER DEFAULT 60,
        bond INTEGER DEFAULT 0,
        xp INTEGER DEFAULT 0,
        last_action_text TEXT DEFAULT 'The dragon is waiting for care.'
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS players (
        guild_id INTEGER,
        user_id INTEGER,
        tokens INTEGER DEFAULT 0,
        points INTEGER DEFAULT 0,
        PRIMARY KEY (guild_id, user_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS cooldowns (
        guild_id INTEGER,
        user_id INTEGER,
        action TEXT,
        last_used TEXT,
        PRIMARY KEY (guild_id, user_id, action)
    )
    """)

    con.commit()
    con.close()


def ensure_dragon(guild_id: int):
    con = db()
    cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO dragon (guild_id) VALUES (?)", (guild_id,))
    con.commit()
    con.close()


def get_dragon(guild_id: int):
    ensure_dragon(guild_id)
    con = db()
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM dragon WHERE guild_id = ?", (guild_id,))
    row = cur.fetchone()
    con.close()
    return row


def get_stage(xp: int):
    if xp >= 5000:
        return "Ancient Dragon", "👑"
    if xp >= 2500:
        return "Adult Dragon", "🔥"
    if xp >= 1000:
        return "Young Dragon", "🐉"
    if xp >= 250:
        return "Hatchling", "🐲"
    return "Egg", "🥚"


def clamp(value):
    return max(0, min(100, value))


def progress_to_next(xp: int):
    stages = [0, 250, 1000, 2500, 5000]
    for needed in stages:
        if xp < needed:
            previous = stages[stages.index(needed) - 1]
            return int(((xp - previous) / (needed - previous)) * 100), needed
    return 100, 5000


# ---------------- EMBED ----------------

def make_embed(guild_id: int):
    d = get_dragon(guild_id)
    stage, emoji = get_stage(d["xp"])
    progress, next_xp = progress_to_next(d["xp"])

    embed = discord.Embed(
        title=f"{emoji} Guild Dragon",
        description=f"**Stage:** {stage}\n**Guild XP:** {d['xp']} / {next_xp}\n**Growth progress:** {progress}%",
        color=0x7B2CFF
    )

    embed.add_field(name="🍖 Hunger", value=f"{d['hunger']}%", inline=True)
    embed.add_field(name="😊 Happiness", value=f"{d['happiness']}%", inline=True)
    embed.add_field(name="⚡ Energy", value=f"{d['energy']}%", inline=True)
    embed.add_field(name="💧 Cleanliness", value=f"{d['cleanliness']}%", inline=True)
    embed.add_field(name="❤️ Bond", value=f"{d['bond']}%", inline=True)

    embed.add_field(
        name="Last action",
        value=d["last_action_text"],
        inline=False
    )

    image_url = STAGE_IMAGES.get(stage)
    if image_url:
        embed.set_image(url=image_url)

    embed.set_footer(text="Use the buttons below to take care of the dragon.")
    return embed


async def update_dragon_message(guild: discord.Guild):
    d = get_dragon(guild.id)
    if not d["channel_id"] or not d["message_id"]:
        return

    channel = guild.get_channel(d["channel_id"])
    if not channel:
        return

    try:
        msg = await channel.fetch_message(d["message_id"])
        await msg.edit(embed=make_embed(guild.id), view=DragonView())
    except Exception:
        pass


# ---------------- COOLDOWNS ----------------

def check_cooldown(guild_id: int, user_id: int, action: str, minutes: int = 30):
    con = db()
    cur = con.cursor()
    cur.execute("""
        SELECT last_used FROM cooldowns
        WHERE guild_id = ? AND user_id = ? AND action = ?
    """, (guild_id, user_id, action))
    row = cur.fetchone()

    now = datetime.now(timezone.utc)

    if row:
        last = datetime.fromisoformat(row[0])
        remaining = timedelta(minutes=minutes) - (now - last)
        if remaining.total_seconds() > 0:
            con.close()
            return False, int(remaining.total_seconds() // 60) + 1

    cur.execute("""
        INSERT OR REPLACE INTO cooldowns (guild_id, user_id, action, last_used)
        VALUES (?, ?, ?, ?)
    """, (guild_id, user_id, action, now.isoformat()))

    con.commit()
    con.close()
    return True, 0


def add_player_reward(guild_id: int, user_id: int, tokens: int, points: int):
    con = db()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO players (guild_id, user_id, tokens, points)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(guild_id, user_id)
        DO UPDATE SET
            tokens = tokens + excluded.tokens,
            points = points + excluded.points
    """, (guild_id, user_id, tokens, points))
    con.commit()
    con.close()


def apply_action(guild_id: int, user: discord.User, action: str):
    effects = {
        "feed":  {"hunger": 15, "xp": 5,  "tokens": 10, "points": 10, "text": "fed the dragon 🍖"},
        "play":  {"happiness": 12, "energy": -5, "xp": 5, "tokens": 10, "points": 10, "text": "played with the dragon 🎾"},
        "train": {"bond": 7, "energy": -10, "xp": 10, "tokens": 15, "points": 15, "text": "trained the dragon 🏋️"},
        "clean": {"cleanliness": 15, "xp": 5, "tokens": 10, "points": 10, "text": "cleaned the dragon 🛁"},
        "rest":  {"energy": 20, "xp": 3, "tokens": 5, "points": 5, "text": "let the dragon rest 😴"},
        "bond":  {"bond": 12, "happiness": 5, "xp": 5, "tokens": 10, "points": 10, "text": "bonded with the dragon ❤️"},
    }

    e = effects[action]

    con = db()
    cur = con.cursor()
    current = get_dragon(guild_id)

    hunger = clamp(current["hunger"] + e.get("hunger", 0))
    happiness = clamp(current["happiness"] + e.get("happiness", 0))
    energy = clamp(current["energy"] + e.get("energy", 0))
    cleanliness = clamp(current["cleanliness"] + e.get("cleanliness", 0))
    bond = clamp(current["bond"] + e.get("bond", 0))
    xp = current["xp"] + e.get("xp", 0)

    text = f"**{user.display_name}** {e['text']} and earned **{e['tokens']} Dragon Tokens**."

    cur.execute("""
        UPDATE dragon
        SET hunger=?, happiness=?, energy=?, cleanliness=?, bond=?, xp=?, last_action_text=?
        WHERE guild_id=?
    """, (hunger, happiness, energy, cleanliness, bond, xp, text, guild_id))

    con.commit()
    con.close()

    add_player_reward(guild_id, user.id, e["tokens"], e["points"])
    return text, e["tokens"]


# ---------------- BUTTONS ----------------

class DragonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def handle(self, interaction: discord.Interaction, action: str):
        ok, mins = check_cooldown(interaction.guild.id, interaction.user.id, action, 30)
        if not ok:
            await interaction.response.send_message(
                f"⏳ You can use **{action}** again in **{mins} minutes**.",
                ephemeral=True
            )
            return

        text, tokens = apply_action(interaction.guild.id, interaction.user, action)
        await interaction.response.edit_message(embed=make_embed(interaction.guild.id), view=DragonView())

    @discord.ui.button(label="Feed", emoji="🍖", style=discord.ButtonStyle.danger, custom_id="dragon_feed")
    async def feed(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle(interaction, "feed")

    @discord.ui.button(label="Play", emoji="🎾", style=discord.ButtonStyle.success, custom_id="dragon_play")
    async def play(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle(interaction, "play")

    @discord.ui.button(label="Train", emoji="🏋️", style=discord.ButtonStyle.primary, custom_id="dragon_train")
    async def train(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle(interaction, "train")

    @discord.ui.button(label="Clean", emoji="🛁", style=discord.ButtonStyle.secondary, custom_id="dragon_clean")
    async def clean(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle(interaction, "clean")

    @discord.ui.button(label="Rest", emoji="😴", style=discord.ButtonStyle.secondary, custom_id="dragon_rest")
    async def rest(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle(interaction, "rest")

    @discord.ui.button(label="Bond", emoji="❤️", style=discord.ButtonStyle.success, custom_id="dragon_bond")
    async def bond(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle(interaction, "bond")

    @discord.ui.button(label="Leaderboard", emoji="🏆", style=discord.ButtonStyle.primary, custom_id="dragon_leaderboard")
    async def leaderboard(self, interaction: discord.Interaction, button: discord.ui.Button):
        con = db()
        cur = con.cursor()
        cur.execute("""
            SELECT user_id, points, tokens FROM players
            WHERE guild_id = ?
            ORDER BY points DESC
            LIMIT 10
        """, (interaction.guild.id,))
        rows = cur.fetchall()
        con.close()

        if not rows:
            await interaction.response.send_message("No leaderboard yet.", ephemeral=True)
            return

        lines = []
        for i, (user_id, points, tokens) in enumerate(rows, start=1):
            user = interaction.guild.get_member(user_id)
            name = user.display_name if user else f"User {user_id}"
            lines.append(f"**{i}. {name}** — {points} points | {tokens} tokens")

        await interaction.response.send_message(
            "🏆 **Top Dragon Keepers**\n\n" + "\n".join(lines),
            ephemeral=True
        )


# ---------------- SETUP COMMAND ----------------

@bot.tree.command(name="dragon_setup", description="Create the live Guild Dragon message in this channel.")
@app_commands.checks.has_permissions(manage_guild=True)
async def dragon_setup(interaction: discord.Interaction):
    ensure_dragon(interaction.guild.id)

    embed = make_embed(interaction.guild.id)
    await interaction.response.send_message("Creating Guild Dragon message...", ephemeral=True)

    msg = await interaction.channel.send(embed=embed, view=DragonView())

    con = db()
    cur = con.cursor()
    cur.execute("""
        UPDATE dragon
        SET channel_id = ?, message_id = ?
        WHERE guild_id = ?
    """, (interaction.channel.id, msg.id, interaction.guild.id))
    con.commit()
    con.close()


@dragon_setup.error
async def dragon_setup_error(interaction: discord.Interaction, error):
    await interaction.response.send_message(
        "You need **Manage Server** permission to set up the dragon.",
        ephemeral=True
    )


@bot.event
async def on_ready():
    init_db()
    bot.add_view(DragonView())
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")


if not TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN in .env file")

bot.run(TOKEN)
