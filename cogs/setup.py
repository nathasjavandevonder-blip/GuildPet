import discord
from discord.ext import commands
from discord import app_commands

from database import ensure_dragon, connect
from embeds import make_dragon_embed
from memories import add_memory
from views.dragon_view import DragonView

class SetupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dragon_setup", description="Create the live Guild Dragon message in this channel.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def dragon_setup(self, interaction: discord.Interaction):
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

async def setup(bot):
    await bot.add_cog(SetupCog(bot))
