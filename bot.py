import asyncio
import discord
from discord.ext import commands, tasks

from config import TOKEN, BOT_OWNER_ID
from database import init_db, get_dragon
from dragon import decay_dragon
from events import random_event_embed, create_event_record
from living import living_update, should_request_care, mark_care_request_sent
from daily_gift import DailyGiftView, daily_gift_available
from views.dragon_view import DragonView
from views.event_view import EventView
from views.updater import update_dragon_message

VERSION = "3.1 Adventure Buttons + Owner Commands"

EXTENSIONS = [
    "cogs.setup",
    "cogs.admin",
    "cogs.progression",
    "cogs.profile",
    "cogs.adventures", "cogs.v5",
]

intents = discord.Intents.default()
intents.members = True


async def owner_only_interaction_check(interaction: discord.Interaction) -> bool:
    """Allow only BOT_OWNER_ID to run slash commands.

    Buttons/select menus remain usable for everyone because they are not
    app command interactions.
    """
    if interaction.command is None:
        return True

    if BOT_OWNER_ID and interaction.user.id == BOT_OWNER_ID:
        return True

    await interaction.response.send_message(
        "⛔ Only Nathasja can use slash commands.",
        ephemeral=True,
    )
    return False


class GuildDragonBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        init_db()

        self.add_view(DragonView())
        self.add_view(EventView())
        self.add_view(DailyGiftView())

        self.tree.interaction_check = owner_only_interaction_check

        for extension in EXTENSIONS:
            try:
                await self.load_extension(extension)
                print(f"Loaded extension: {extension}")
            except Exception as exc:
                print(f"Failed to load extension {extension}: {exc}")
                raise

        synced = await self.tree.sync()
        print(f"Synced {len(synced)} commands")

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        print(f"Guild Dragon Bot v{VERSION}")

        for guild in self.guilds:
            try:
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                print(f"Synced {len(synced)} commands to guild: {guild.name}")
            except Exception as exc:
                print(f"Guild sync failed for {guild.name}: {exc}")

        if not dragon_decay.is_running():
            dragon_decay.start()
        if not random_events.is_running():
            random_events.start()
        if not living_dragon.is_running():
            living_dragon.start()
        if not daily_gift_task.is_running():
            daily_gift_task.start()


bot = GuildDragonBot()


@tasks.loop(minutes=30)
async def dragon_decay():
    for guild in bot.guilds:
        try:
            decay_dragon(guild.id)
            await update_dragon_message(guild)
        except Exception as exc:
            print(f"dragon_decay failed in {guild.name}: {exc}")


@tasks.loop(minutes=20)
async def random_events():
    for guild in bot.guilds:
        try:
            import random

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
            await update_dragon_message(guild)
        except Exception as exc:
            print(f"random_events failed in {guild.name}: {exc}")


@tasks.loop(minutes=15)
async def living_dragon():
    for guild in bot.guilds:
        try:
            living_update(guild.id)
            await update_dragon_message(guild)

            should_send, care_message = should_request_care(guild.id)
            if should_send:
                d = get_dragon(guild.id)
                channel_id = d["channel_id"]
                channel = guild.get_channel(channel_id) if channel_id else None
                if channel:
                    await channel.send(care_message, delete_after=1800)
                    mark_care_request_sent(guild.id)
        except Exception as exc:
            print(f"living_dragon failed in {guild.name}: {exc}")


@tasks.loop(hours=3)
async def daily_gift_task():
    for guild in bot.guilds:
        try:
            if not daily_gift_available(guild.id):
                continue

            d = get_dragon(guild.id)
            channel_id = d["channel_id"]
            if not channel_id:
                continue

            channel = guild.get_channel(channel_id)
            if not channel:
                continue

            await channel.send(
                "🎁 **Daily Guild Gift**\nThe dragon found treasure for the guild!",
                view=DailyGiftView(),
            )
        except Exception as exc:
            print(f"daily_gift_task failed in {guild.name}: {exc}")


if not TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN or TOKEN in .env file")

bot.run(TOKEN)
