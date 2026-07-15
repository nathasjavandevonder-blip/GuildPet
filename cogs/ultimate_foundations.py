from __future__ import annotations

import random

import discord
from discord import app_commands
from discord.ext import commands

from systems.onboarding.service import EGGS, get_lifecycle, get_setup, resolve_lifecycle
from ui.management_panel import (
    OWNER_ID,
    DeveloperPanel,
    ManagementPanel,
    build_developer_embed,
    build_management_embed,
)
from ui.setup_wizard import SetupWizardView


class UltimateFoundations(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="guildpet_setup", description="Configure or manage GuildPet for this server.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def guildpet_setup(self, interaction: discord.Interaction) -> None:
        setup = get_setup(interaction.guild_id)
        if setup is not None and setup["setup_complete"]:
            await interaction.response.send_message(
                embed=build_management_embed(interaction.guild),
                view=ManagementPanel(show_developer=interaction.user.id == OWNER_ID),
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="🐉 GuildPet Ultimate Setup",
            description=(
                "Choose the main dragon channel, welcome channel, allowed AI-chat channels and activity level.\n\n"
                "When you finish, the guild-wide egg vote begins. Every egg is available to every guild."
            ),
            color=discord.Color.blurple(),
        )
        await interaction.response.send_message(embed=embed, view=SetupWizardView(), ephemeral=True)

    @app_commands.command(name="guildpet_manage", description="Open the GuildPet management panel.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def guildpet_manage(self, interaction: discord.Interaction) -> None:
        setup = get_setup(interaction.guild_id)
        if setup is None or not setup["setup_complete"]:
            await interaction.response.send_message("Run `/guildpet_setup` first.", ephemeral=True)
            return
        await interaction.response.send_message(
            embed=build_management_embed(interaction.guild),
            view=ManagementPanel(show_developer=interaction.user.id == OWNER_ID),
            ephemeral=True,
        )

    @app_commands.command(name="guildpet_dev", description="Owner-only GuildPet testing panel.")
    async def guildpet_dev(self, interaction: discord.Interaction) -> None:
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("This command is restricted to the GuildPet owner.", ephemeral=True)
            return
        await interaction.response.send_message(
            embed=build_developer_embed(interaction.guild),
            view=DeveloperPanel(),
            ephemeral=True,
        )

    @app_commands.command(name="guildpet_lifecycle", description="Show the current dragon growth stage and egg choice.")
    async def guildpet_lifecycle(self, interaction: discord.Interaction) -> None:
        lifecycle = resolve_lifecycle(interaction.guild_id)
        egg = EGGS.get(lifecycle.selected_egg or "")
        embed = discord.Embed(title="🐉 Dragon Lifecycle", color=discord.Color.teal())
        embed.add_field(name="Stage", value=lifecycle.stage.replace("_", " ").title(), inline=False)
        embed.add_field(name="Egg", value=egg[0] if egg else "Not chosen yet", inline=False)
        embed.add_field(
            name="Progression rule",
            value="Egg care first. Hatchling care unlocks next. Travel and combat unlock when the dragon reaches the Young stage.",
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        if member.bot:
            return
        setup = get_setup(member.guild.id)
        if setup is None or not setup["setup_complete"] or not setup["welcome_enabled"]:
            return
        channel_id = setup["welcome_channel_id"] or setup["dragon_channel_id"]
        channel = member.guild.get_channel(int(channel_id)) if channel_id else None
        if channel is None:
            return
        lifecycle = resolve_lifecycle(member.guild.id)
        if lifecycle.stage == "egg_vote":
            text = f"🥚 Welcome, {member.mention}! Our guild is choosing which ancient egg to protect. Your vote matters too."
        elif lifecycle.stage == "incubating":
            text = f"🥚 *The egg wiggles softly as {member.mention} arrives.* Another keeper has joined us."
        elif lifecycle.stage == "hatchling":
            text = f"🐣 Hi {member.mention}! I am still little, but I hope we can become friends."
        else:
            text = random.choice([
                f"🐉 Welcome, {member.mention}! Our dragon is curious to meet you.",
                f"🐉 A new keeper has arrived. Welcome to the guild, {member.mention}!",
            ])
        try:
            await channel.send(text, allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))
        except (discord.Forbidden, discord.HTTPException):
            pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(UltimateFoundations(bot))
