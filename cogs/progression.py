import discord
from discord.ext import commands
from discord import app_commands

from embeds import make_world_embed, make_research_embed, make_progression_embed
from progression import prestige_guild
from views.research_view import ResearchView
from views.updater import update_dragon_message

class ProgressionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dragon_world", description="Show the guild's dragon world progression.")
    async def dragon_world(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=make_world_embed(interaction.guild.id),
            ephemeral=True
        )

    @app_commands.command(name="dragon_research", description="Open the dragon research menu.")
    async def dragon_research(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=make_research_embed(interaction.guild.id),
            view=ResearchView(),
            ephemeral=True
        )

    @app_commands.command(name="dragon_progression", description="Show guild progression, level and research.")
    async def dragon_progression(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=make_progression_embed(interaction.guild.id),
            ephemeral=True
        )

    @app_commands.command(name="dragon_prestige", description="Prestige the guild dragon progression at level 25.")
    @app_commands.checks.has_permissions(administrator=True)
    async def dragon_prestige(self, interaction: discord.Interaction):
        ok, msg = prestige_guild(interaction.guild.id)
        await update_dragon_message(interaction.guild)
        await interaction.response.send_message(msg, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ProgressionCog(bot))
