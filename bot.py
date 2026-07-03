import random
import discord
from discord.ext import commands, tasks
from discord import app_commands

from config import TOKEN
from database import init_db, ensure_dragon, connect, get_dragon
from embeds import make_dragon_embed
from memories import add_memory
from dragon import decay_dragon
from events import random_event_embed, create_event_record
from views.dragon_view import DragonView
from views.event_view import EventView
from views.updater import update_dragon_message

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.tree.command(name="dragon_setup", description="Create the live Guild Dragon message in this channel.")
@app_commands.checks.has_permissions(manage_guild=True)
async def dragon_setup(interaction: discord.Interaction):
    ensure_dragon(interaction.guild.id)
    await interaction.response.send_message("Creating Guild Dragon message...", ephemeral=True)

    embed, file = make_dragon_embed(interaction.guild.id)
    if file:
        msg = await interaction.channel.send(embed=embed, file=file, view=DragonView())
    else:
        msg = await interaction.channel.send(embed=embed, view=DragonView())

    con = connect()
    cur = con.cursor()
    cur.execute("""
        UPDATE dragon
        SET channel_id = ?, message_id = ?, event_channel_id = ?
        WHERE guild_id = ?
    """, (interaction.channel.id, msg.id, interaction.channel.id, interaction.guild.id))
    con.commit()
    con.close()

    add_memory(interaction.guild.id, f"The Guild Dragon was born in #{interaction.channel.name}.")


@bot.tree.command(name="dragon_event_channel", description="Set the channel for random dragon events.")
@app_commands.checks.has_permissions(manage_guild=True)
async def dragon_event_channel(interaction: discord.Interaction):
    ensure_dragon(interaction.guild.id)

    con = connect()
    cur = con.cursor()
    cur.execute("UPDATE dragon SET event_channel_id=? WHERE guild_id=?", (interaction.channel.id, interaction.guild.id))
    con.commit()
    con.close()

    await interaction.response.send_message("✅ Random dragon events will appear in this channel.", ephemeral=True)


@bot.tree.command(name="dragon_reset", description="Reset the Guild Dragon data. Careful!")
@app_commands.checks.has_permissions(administrator=True)
async def dragon_reset(interaction: discord.Interaction):
    con = connect()
    cur = con.cursor()
    for table in ["dragon", "players", "cooldowns", "shop_items", "achievements", "memories", "events"]:
        cur.execute(f"DELETE FROM {table} WHERE guild_id=?", (interaction.guild.id,))
    con.commit()
    con.close()
    await interaction.response.send_message("✅ Guild Dragon data has been reset.", ephemeral=True)


@tasks.loop(minutes=30)
async def dragon_decay():
    for guild in bot.guilds:
        decay_dragon(guild.id)
        await update_dragon_message(guild)


@tasks.loop(minutes=20)
async def random_events():
    for guild in bot.guilds:
        if random.random() > 0.10:
            continue

        d = get_dragon(guild.id)
        channel_id = d["event_channel_id"] or d["channel_id"]
        if not channel_id:
            continue

        channel = guild.get_channel(channel_id)
        if not channel:
            continue

        event_type, embed = random_event_embed()
        msg = await channel.send(embed=embed, view=EventView())
        create_event_record(guild.id, event_type, msg.id)


@bot.event
async def on_ready():
    init_db()
    bot.add_view(DragonView())
    bot.add_view(EventView())

    if not dragon_decay.is_running():
        dragon_decay.start()
    if not random_events.is_running():
        random_events.start()

    await bot.tree.sync()
    print(f"Logged in as {bot.user}")


if not TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN or TOKEN in .env file")

bot.run(TOKEN)
