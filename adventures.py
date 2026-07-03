import discord
from discord.ext import commands
from discord import app_commands

from adventures import make_adventure_embed, adventure_status_text
from views.adventure_view import AdventureView

class AdventuresCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dragon_adventures", description="Send the guild dragon on adventures.")
    async def dragon_adventures(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=make_adventure_embed(interaction.guild.id),
            view=AdventureView(),
            ephemeral=True
        )

    @app_commands.command(name="dragon_adventure_status", description="Show the dragon's current adventure status.")
    async def dragon_adventure_status(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            adventure_status_text(interaction.guild.id),
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(AdventuresCog(bot))
