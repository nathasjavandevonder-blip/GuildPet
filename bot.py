import random
import discord
from discord.ext import commands, tasks
from discord import app_commands

from config import TOKEN
from database import init_db, ensure_dragon, connect, get_dragon
from embeds import (
    make_dragon_embed,
    make_profile_embed,
    make_art_status_embed,
    make_needed_images_embed,
    make_world_embed,
    make_research_embed,
    make_progression_embed,
    make_trait_embed,
)
from memories import add_memory
from dragon import decay_dragon
from events import random_event_embed, create_event_record
from living import living_update, should_request_care, mark_care_request_sent
from progression import prestige_guild
from daily_gift import DailyGiftView, daily_gift_available
from views.dragon_view import DragonView
from views.event_view import EventView
from views.updater import update_dragon_message

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

async def set_dragon_field(interaction, field, value, msg, memory=None):
    ensure_dragon(interaction.guild.id)

    con = connect()
    cur = con.cursor()
    cur.execute(
        f"UPDATE dragon SET {field}=?, dragon_message=?, last_action_text=? WHERE guild_id=?",
        (value, msg, msg, interaction.guild.id)
    )
    con.commit()
    con.close()

    if memory:
        add_memory(interaction.guild.id, memory)

    await update_dragon_message(interaction.guild)
    await interaction.response.send_message(f"✅ Updated **{field}** to **{value}**.", ephemeral=True)

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
    cur.execute(
        "UPDATE dragon SET channel_id=?, message_id=?, event_channel_id=? WHERE guild_id=?",
        (interaction.channel.id, msg.id, interaction.channel.id, interaction.guild.id)
    )
    con.commit()
    con.close()

    add_memory(interaction.guild.id, f"The Guild Dragon was born in #{interaction.channel.name}.")

@bot.tree.command(name="dragon_world", description="Show the guild's dragon world progression.")
async def dragon_world(interaction: discord.Interaction):
    await interaction.response.send_message(
        embed=make_world_embed(interaction.guild.id),
        ephemeral=True
    )

@bot.tree.command(name="dragon_research", description="Open the dragon research menu.")
async def dragon_research(interaction: discord.Interaction):
    from views.research_view import ResearchView

    await interaction.response.send_message(
        embed=make_research_embed(interaction.guild.id),
        view=ResearchView(),
        ephemeral=True
    )

@bot.tree.command(name="dragon_progression", description="Show guild progression, level and research.")
async def dragon_progression(interaction: discord.Interaction):
    await interaction.response.send_message(
        embed=make_progression_embed(interaction.guild.id),
        ephemeral=True
    )

@bot.tree.command(name="dragon_prestige", description="Prestige the guild dragon progression at level 25.")
@app_commands.checks.has_permissions(administrator=True)
async def dragon_prestige(interaction: discord.Interaction):
    ok, msg = prestige_guild(interaction.guild.id)
    await update_dragon_message(interaction.guild)
    await interaction.response.send_message(msg, ephemeral=True)

@bot.tree.command(name="dragon_name", description="Rename your guild dragon.")
@app_commands.checks.has_permissions(manage_guild=True)
async def dragon_name(interaction: discord.Interaction, name: str):
    if len(name) > 32:
        await interaction.response.send_message("Name is too long. Max 32 characters.", ephemeral=True)
        return

    await set_dragon_field(
        interaction,
        "dragon_name",
        name,
        f"🐉 My name is {name} now!",
        f"The guild named the dragon {name}."
    )

@bot.tree.command(name="dragon_color", description="Set your guild dragon color.")
@app_commands.checks.has_permissions(manage_guild=True)
async def dragon_color(interaction: discord.Interaction, color: str):
    if len(color) > 24:
        await interaction.response.send_message("Color name is too long. Max 24 characters.", ephemeral=True)
        return

    await set_dragon_field(
        interaction,
        "dragon_color",
        color,
        f"🎨 I feel like a {color} dragon.",
        f"The dragon became a {color} dragon."
    )

@bot.tree.command(name="dragon_accessory", description="Set the dragon accessory.")
@app_commands.checks.has_permissions(manage_guild=True)
async def dragon_accessory(interaction: discord.Interaction, accessory: str):
    if len(accessory) > 32:
        await interaction.response.send_message("Accessory name is too long. Max 32 characters.", ephemeral=True)
        return

    await set_dragon_field(
        interaction,
        "accessory",
        accessory,
        f"🎩 Do you like my {accessory}?",
        f"The dragon received an accessory: {accessory}."
    )

@bot.tree.command(name="dragon_weather", description="Set dragon lair weather manually.")
@app_commands.checks.has_permissions(manage_guild=True)
async def dragon_weather(interaction: discord.Interaction, weather: str):
    if len(weather) > 24:
        await interaction.response.send_message("Weather name is too long. Max 24 characters.", ephemeral=True)
        return

    await set_dragon_field(
        interaction,
        "weather",
        weather,
        f"🌤️ The weather is {weather} around the lair."
    )

@bot.tree.command(name="dragon_force_pose", description="Force the dragon pose for testing images.")
@app_commands.checks.has_permissions(manage_guild=True)
async def dragon_force_pose(interaction: discord.Interaction, pose: str):
    await set_dragon_field(interaction, "pose", pose, f"🎭 Testing pose: {pose}.")

@bot.tree.command(name="dragon_force_stats", description="Force dragon stats for testing.")
@app_commands.checks.has_permissions(administrator=True)
async def dragon_force_stats(interaction: discord.Interaction, hunger: int, happiness: int, energy: int, cleanliness: int, bond: int):
    from utils import clamp

    con = connect()
    cur = con.cursor()
    cur.execute("""
        UPDATE dragon
        SET hunger=?,
            happiness=?,
            energy=?,
            cleanliness=?,
            bond=?,
            dragon_message=?,
            last_action_text=?
        WHERE guild_id=?
    """, (
        clamp(hunger),
        clamp(happiness),
        clamp(energy),
        clamp(cleanliness),
        clamp(bond),
        "My stats changed suddenly!",
        "🧪 Dragon stats were adjusted for testing.",
        interaction.guild.id
    ))
    con.commit()
    con.close()

    await update_dragon_message(interaction.guild)
    await interaction.response.send_message("✅ Test stats updated.", ephemeral=True)

@bot.tree.command(name="dragon_add_tokens", description="Add guild tokens for testing shop/world.")
@app_commands.checks.has_permissions(administrator=True)
async def dragon_add_tokens(interaction: discord.Interaction, amount: int):
    con = connect()
    cur = con.cursor()
    cur.execute("""
        UPDATE dragon
        SET guild_tokens=guild_tokens+?,
            lifetime_guild_tokens=lifetime_guild_tokens+?,
            dragon_message=?,
            last_action_text=?
        WHERE guild_id=?
    """, (
        amount,
        amount,
        "The guild treasure pile grew!",
        f"🪙 Added {amount} Guild Tokens for testing.",
        interaction.guild.id
    ))
    con.commit()
    con.close()

    await update_dragon_message(interaction.guild)
    await interaction.response.send_message(f"✅ Added **{amount}** Guild Tokens.", ephemeral=True)

@bot.tree.command(name="dragon_art_status", description="Show what image files the art engine is looking for.")
async def dragon_art_status(interaction: discord.Interaction):
    await interaction.response.send_message(
        embed=make_art_status_embed(interaction.guild.id),
        ephemeral=True
    )

@bot.tree.command(name="dragon_needed_images", description="Show needed image filenames for the current dragon stage.")
async def dragon_needed_images(interaction: discord.Interaction):
    await interaction.response.send_message(
        embed=make_needed_images_embed(interaction.guild.id),
        ephemeral=True
    )

@bot.tree.command(name="dragon_living_status", description="Show the dragon's current living state.")
async def dragon_living_status(interaction: discord.Interaction):
    d = get_dragon(interaction.guild.id)

    await interaction.response.send_message(
        f"🐉 **Living Dragon Status**\n"
        f"Pose: **{d['pose']}**\n"
        f"Sleeping: **{'Yes' if d['sleeping'] else 'No'}**\n"
        f"Last living update: **{d['last_living_update'] or 'Never'}**\n"
        f"Last care request: **{d['last_care_request'] or 'Never'}**\n"
        f"Dragon says: *\"{d['dragon_message']}\"*",
        ephemeral=True
    )


@bot.tree.command(name="dragon_trait", description="Show the dragon's permanent trait.")
async def dragon_trait(interaction: discord.Interaction):
    await interaction.response.send_message(
        embed=make_trait_embed(interaction.guild.id),
        ephemeral=True
    )

@bot.tree.command(name="dragon_profile", description="Show your dragon keeper profile.")
async def dragon_profile(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user

    await interaction.response.send_message(
        embed=make_profile_embed(interaction.guild, member),
        ephemeral=True
    )

@bot.tree.command(name="dragon_title", description="Set your personal dragon keeper title.")
async def dragon_title(interaction: discord.Interaction, title: str):
    if len(title) > 32:
        await interaction.response.send_message("Title is too long. Max 32 characters.", ephemeral=True)
        return

    con = connect()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO players (guild_id, user_id, keeper_title)
        VALUES (?, ?, ?)
        ON CONFLICT(guild_id, user_id)
        DO UPDATE SET keeper_title=excluded.keeper_title
    """, (interaction.guild.id, interaction.user.id, title))
    con.commit()
    con.close()

    await interaction.response.send_message(f"✅ Your keeper title is now **{title}**.", ephemeral=True)

@bot.tree.command(name="dragon_streak", description="Show your current dragon keeper streak.")
async def dragon_streak(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user

    con = connect()
    con.row_factory = __import__("sqlite3").Row
    cur = con.cursor()
    cur.execute(
        "SELECT streak, best_streak, last_daily FROM players WHERE guild_id=? AND user_id=?",
        (interaction.guild.id, member.id)
    )
    p = cur.fetchone()
    con.close()

    if not p:
        await interaction.response.send_message(f"{member.display_name} has no streak yet.", ephemeral=True)
        return

    await interaction.response.send_message(
        f"🔥 **{member.display_name}'s Keeper Streak**\n"
        f"Current: **{p['streak']} days**\n"
        f"Best: **{p['best_streak']} days**\n"
        f"Last care day: **{p['last_daily'] or 'Never'}**",
        ephemeral=True
    )

@bot.tree.command(name="dragon_event_channel", description="Set the channel for random dragon events.")
@app_commands.checks.has_permissions(manage_guild=True)
async def dragon_event_channel(interaction: discord.Interaction):
    ensure_dragon(interaction.guild.id)

    con = connect()
    cur = con.cursor()
    cur.execute(
        "UPDATE dragon SET event_channel_id=? WHERE guild_id=?",
        (interaction.channel.id, interaction.guild.id)
    )
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

@tasks.loop(minutes=15)
async def living_dragon():
    for guild in bot.guilds:
        reason, message = living_update(guild.id)
        await update_dragon_message(guild)

        should_send, care_message = should_request_care(guild.id)

        if should_send:
            d = get_dragon(guild.id)
            channel_id = d["channel_id"]
            channel = guild.get_channel(channel_id) if channel_id else None

            if channel:
                try:
                    await channel.send(care_message, delete_after=1800)
                    mark_care_request_sent(guild.id)
                except Exception:
                    pass


@tasks.loop(hours=3)
async def daily_gift_task():
    for guild in bot.guilds:
        if not daily_gift_available(guild.id):
            continue

        d = get_dragon(guild.id)
        channel_id = d["channel_id"]

        if not channel_id:
            continue

        channel = guild.get_channel(channel_id)

        if not channel:
            continue

        try:
            await channel.send(
                "🎁 **Daily Guild Gift**\nThe dragon found treasure for the guild!",
                view=DailyGiftView()
            )
        except Exception:
            pass

@bot.event
async def on_ready():
    init_db()
    bot.add_view(DragonView())
    bot.add_view(EventView())
    bot.add_view(DailyGiftView())

    if not dragon_decay.is_running():
        dragon_decay.start()

    if not random_events.is_running():
        random_events.start()

    if not living_dragon.is_running():
        living_dragon.start()

    if not daily_gift_task.is_running():
        daily_gift_task.start()

    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

if not TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN or TOKEN in .env file")

bot.run(TOKEN)
