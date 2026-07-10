from __future__ import annotations

import os

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from core.config import BASE_DIR
from migrations.manager import run_migrations
from systems.adventures.catalog import load_adventures
from systems.adventures.service import start_adventure
from systems.chronicle.service import get_chronicle
from systems.combat.service import start_combat
from systems.living.service import get_living_state
from systems.state.models import DragonState
from systems.state.service import ensure_state, get_state
from ui.view_manager import build_view
from ui.views.achievement_view import (
    AchievementHallView,
    build_achievement_embed,
)
from ui.views.adventure_view import build_adventure_embed
from ui.views.combat_view import build_combat_embed


load_dotenv(BASE_DIR / ".env.v5", override=True)

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing from .env.v5")


def build_main_embed(guild_id: int) -> discord.Embed:
    living = get_living_state(guild_id)
    state = ensure_state(guild_id)

    state_names = {
        DragonState.IDLE: "Relaxing",
        DragonState.SLEEPING: "Sleeping",
        DragonState.ADVENTURE: "On Adventure",
        DragonState.COMBAT: "In Combat",
        DragonState.RECOVERING: "Recovering",
        DragonState.CELEBRATING: "Celebrating",
    }

    embed = discord.Embed(
        title="🐉 GuildPet v5 Alpha",
        description=(
            f"**Current state:** {state_names[state.state]}\n"
            f"**Activity:** {living.current_activity.title()}\n"
            f"**Mood:** {living.mood.value.title()}"
        ),
        color=discord.Color.blurple(),
    )

    embed.add_field(
        name="🍖 Hunger",
        value=f"**{living.hunger}/100**",
        inline=True,
    )
    embed.add_field(
        name="😊 Happiness",
        value=f"**{living.happiness}/100**",
        inline=True,
    )
    embed.add_field(
        name="⚡ Energy",
        value=f"**{living.energy}/100**",
        inline=True,
    )
    embed.add_field(
        name="🛁 Cleanliness",
        value=f"**{living.cleanliness}/100**",
        inline=True,
    )
    embed.add_field(
        name="❤️ Guild Bond",
        value=f"**{living.bond}/100**",
        inline=True,
    )

    embed.set_footer(
        text="GuildPet v5 test environment — data is separate from live"
    )
    return embed


class AdventureSelect(discord.ui.Select):
    def __init__(self):
        adventures = load_adventures()

        options = [
            discord.SelectOption(
                label=adventure.name,
                value=adventure.key,
                emoji=adventure.emoji,
                description=adventure.description[:100],
            )
            for adventure in adventures.values()
        ]

        super().__init__(
            placeholder="Choose an adventure",
            options=options[:25],
            custom_id="v5_test_adventure_select",
        )

    async def callback(
        self,
        interaction: discord.Interaction,
    ) -> None:
        try:
            start_adventure(
                interaction.guild_id,
                user_id=interaction.user.id,
                username=interaction.user.display_name,
                adventure_key=self.values[0],
            )
        except ValueError as exc:
            await interaction.response.send_message(
                str(exc),
                ephemeral=True,
                delete_after=30,
            )
            return

        await interaction.response.edit_message(
            embed=build_adventure_embed(interaction.guild_id),
            view=build_view(interaction.guild_id),
        )


class AdventureStartView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(AdventureSelect())


class V5TestBot(commands.Bot):
    async def setup_hook(self) -> None:
        applied = run_migrations()

        if applied:
            print("Applied migrations:", ", ".join(applied))

        await self.tree.sync()
        print(f"Synced {len(self.tree.get_commands())} application commands.")


intents = discord.Intents.default()
bot = V5TestBot(command_prefix="!", intents=intents)


@bot.event
async def on_ready() -> None:
    print(f"GuildPet v5 testbot connected as {bot.user}")


@bot.tree.command(
    name="v5panel",
    description="Post the GuildPet v5 alpha test panel.",
)
@app_commands.checks.has_permissions(manage_guild=True)
async def v5panel(interaction: discord.Interaction) -> None:
    ensure_state(interaction.guild_id)

    await interaction.response.send_message(
        embed=build_main_embed(interaction.guild_id),
        view=build_view(interaction.guild_id),
    )


@bot.tree.command(
    name="v5refresh",
    description="Refresh the current GuildPet v5 state panel.",
)
async def v5refresh(interaction: discord.Interaction) -> None:
    state = get_state(interaction.guild_id)

    if state.state == DragonState.ADVENTURE:
        embed = build_adventure_embed(interaction.guild_id)
    elif state.state == DragonState.COMBAT:
        embed = build_combat_embed(interaction.guild_id)
    else:
        embed = build_main_embed(interaction.guild_id)

    await interaction.response.send_message(
        embed=embed,
        view=build_view(interaction.guild_id),
        ephemeral=True,
        delete_after=30,
    )


@bot.tree.command(
    name="v5adventure",
    description="Choose an interactive v5 adventure.",
)
async def v5adventure(interaction: discord.Interaction) -> None:
    state = get_state(interaction.guild_id)

    if state.state != DragonState.IDLE:
        await interaction.response.send_message(
            f"The dragon is currently **{state.state.value}**.",
            ephemeral=True,
            delete_after=30,
        )
        return

    await interaction.response.send_message(
        "🗺️ **Choose an adventure destination**",
        view=AdventureStartView(),
        ephemeral=True,
        delete_after=180,
    )


@bot.tree.command(
    name="v5combat",
    description="Start a training combat encounter.",
)
async def v5combat(interaction: discord.Interaction) -> None:
    state = get_state(interaction.guild_id)

    if state.state != DragonState.IDLE:
        await interaction.response.send_message(
            f"The dragon is currently **{state.state.value}**.",
            ephemeral=True,
            delete_after=30,
        )
        return

    start_combat(
        interaction.guild_id,
        enemy_key="training_goblin",
        channel_id=interaction.channel_id,
    )

    await interaction.response.send_message(
        embed=build_combat_embed(interaction.guild_id),
        view=build_view(interaction.guild_id),
    )


@bot.tree.command(
    name="v5achievements",
    description="View and choose your showcase achievement.",
)
async def v5achievements(
    interaction: discord.Interaction,
    member: discord.Member | None = None,
) -> None:
    target = member or interaction.user

    embed = build_achievement_embed(
        interaction.guild_id,
        target.id,
        target.display_name,
    )

    view = (
        AchievementHallView(
            interaction.guild_id,
            interaction.user.id,
        )
        if target.id == interaction.user.id
        else None
    )

    await interaction.response.send_message(
        embed=embed,
        view=view,
        ephemeral=True,
        delete_after=300,
    )


@bot.tree.command(
    name="v5chronicle",
    description="View recent GuildPet v5 guild history.",
)
async def v5chronicle(interaction: discord.Interaction) -> None:
    rows = get_chronicle(
        interaction.guild_id,
        limit=15,
    )

    if not rows:
        await interaction.response.send_message(
            "📖 The Guild Chronicle is still empty.",
            ephemeral=True,
            delete_after=30,
        )
        return

    lines = [
        f"**{row['title']}**\n{row['description']}"
        for row in rows
    ]

    embed = discord.Embed(
        title="📖 Guild Chronicle",
        description="\n\n".join(lines)[:4000],
        color=discord.Color.dark_gold(),
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True,
        delete_after=300,
    )


@v5panel.error
async def v5panel_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
) -> None:
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "Only members with **Manage Server** can post the v5 panel.",
            ephemeral=True,
            delete_after=30,
        )
        return

    raise error


bot.run(TOKEN)
