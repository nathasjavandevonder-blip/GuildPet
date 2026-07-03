import discord
from discord.ext import commands
from discord import app_commands

from database import ensure_dragon, connect, get_dragon
from embeds import make_art_status_embed, make_needed_images_embed
from memories import add_memory
from views.updater import update_dragon_message

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

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dragon_name", description="Rename your guild dragon.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def dragon_name(self, interaction: discord.Interaction, name: str):
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

    @app_commands.command(name="dragon_color", description="Set your guild dragon color.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def dragon_color(self, interaction: discord.Interaction, color: str):
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

    @app_commands.command(name="dragon_accessory", description="Set the dragon accessory.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def dragon_accessory(self, interaction: discord.Interaction, accessory: str):
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

    @app_commands.command(name="dragon_weather", description="Set dragon lair weather manually.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def dragon_weather(self, interaction: discord.Interaction, weather: str):
        if len(weather) > 24:
            await interaction.response.send_message("Weather name is too long. Max 24 characters.", ephemeral=True)
            return

        await set_dragon_field(
            interaction,
            "weather",
            weather,
            f"🌤️ The weather is {weather} around the lair."
        )

    @app_commands.command(name="dragon_force_pose", description="Force the dragon pose for testing images.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def dragon_force_pose(self, interaction: discord.Interaction, pose: str):
        await set_dragon_field(interaction, "pose", pose, f"🎭 Testing pose: {pose}.")

    @app_commands.command(name="dragon_force_stats", description="Force dragon stats for testing.")
    @app_commands.checks.has_permissions(administrator=True)
    async def dragon_force_stats(self, interaction: discord.Interaction, hunger: int, happiness: int, energy: int, cleanliness: int, bond: int):
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

    @app_commands.command(name="dragon_add_tokens", description="Add guild tokens for testing shop/world.")
    @app_commands.checks.has_permissions(administrator=True)
    async def dragon_add_tokens(self, interaction: discord.Interaction, amount: int):
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

    @app_commands.command(name="dragon_art_status", description="Show what image files the art engine is looking for.")
    async def dragon_art_status(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=make_art_status_embed(interaction.guild.id),
            ephemeral=True
        )

    @app_commands.command(name="dragon_needed_images", description="Show needed image filenames for the current dragon stage.")
    async def dragon_needed_images(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=make_needed_images_embed(interaction.guild.id),
            ephemeral=True
        )

    @app_commands.command(name="dragon_event_channel", description="Set the channel for random dragon events.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def dragon_event_channel(self, interaction: discord.Interaction):
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

    @app_commands.command(name="dragon_reset", description="Reset the Guild Dragon data. Careful!")
    @app_commands.checks.has_permissions(administrator=True)
    async def dragon_reset(self, interaction: discord.Interaction):
        con = connect()
        cur = con.cursor()

        for table in ["dragon", "players", "cooldowns", "shop_items", "achievements", "memories", "events"]:
            cur.execute(f"DELETE FROM {table} WHERE guild_id=?", (interaction.guild.id,))

        con.commit()
        con.close()

        await interaction.response.send_message("✅ Guild Dragon data has been reset.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
