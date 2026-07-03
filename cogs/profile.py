import discord
from discord.ext import commands
from discord import app_commands

from database import connect, get_dragon
from embeds import make_profile_embed, make_trait_embed

class ProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dragon_profile", description="Show your dragon keeper profile.")
    async def dragon_profile(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user

        await interaction.response.send_message(
            embed=make_profile_embed(interaction.guild, member),
            ephemeral=True
        )

    @app_commands.command(name="dragon_title", description="Set your personal dragon keeper title.")
    async def dragon_title(self, interaction: discord.Interaction, title: str):
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

    @app_commands.command(name="dragon_streak", description="Show your current dragon keeper streak.")
    async def dragon_streak(self, interaction: discord.Interaction, member: discord.Member = None):
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

    @app_commands.command(name="dragon_living_status", description="Show the dragon's current living state.")
    async def dragon_living_status(self, interaction: discord.Interaction):
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

    @app_commands.command(name="dragon_trait", description="Show the dragon's permanent trait.")
    async def dragon_trait(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=make_trait_embed(interaction.guild.id),
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(ProfileCog(bot))
