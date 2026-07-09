import discord
from discord.ext import commands
from discord import app_commands
from database import connect
from v5_systems import (
    init_v5,
    update_v5_state,
    talk_response,
    record_contribution,
    get_top_contributors,
    get_memories,
    upgrade_lair_room,
    get_lair,
    create_world_event,
)

class V5Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        init_v5()

    @app_commands.command(name="dragon_v5", description="Show GuildPet v5.0 living dragon status.")
    async def dragon_v5(self, interaction: discord.Interaction):
        mood, personality = update_v5_state(interaction.guild.id)
        embed = discord.Embed(
            title="🐉 GuildPet v5.0 — Living Dragon",
            description="The dragon now has mood, personality, memories, relationships, contributions, lair upgrades and world events.",
            color=0xb76cff,
        )
        embed.add_field(name="Mood", value=f"**{mood}**", inline=True)
        embed.add_field(name="Personality", value=f"**{personality}**", inline=True)
        embed.add_field(name="New commands", value="`/dragon_talk`\n`/dragon_pet`\n`/dragon_praise`\n`/dragon_contributions`\n`/dragon_memories_v5`\n`/dragon_lair_v5`\n`/dragon_world_event`", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="dragon_talk", description="Talk with the guild dragon.")
    async def dragon_talk(self, interaction: discord.Interaction):
        text, mood, personality, personal_bond = talk_response(interaction.guild.id, interaction.user)
        record_contribution(interaction.guild.id, interaction.user, "talk", 1)
        embed = discord.Embed(title="💬 The Dragon Speaks", description=text, color=0xb76cff)
        embed.add_field(name="Mood", value=mood, inline=True)
        embed.add_field(name="Personality", value=personality, inline=True)
        embed.add_field(name="Your bond", value=str(personal_bond), inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dragon_pet", description="Pet the guild dragon.")
    async def dragon_pet(self, interaction: discord.Interaction):
        record_contribution(interaction.guild.id, interaction.user, "pet", 2)
        con = connect()
        cur = con.cursor()
        cur.execute("UPDATE dragon SET happiness=MIN(happiness+3,100), bond=MIN(bond+2,100), dragon_message=? WHERE guild_id=?",
                    (f"{interaction.user.display_name} petted me. I feel loved.", interaction.guild.id))
        con.commit()
        con.close()
        await interaction.response.send_message(f"🐉 {interaction.user.display_name} gently petted the dragon. It looks happy.")

    @app_commands.command(name="dragon_praise", description="Praise the guild dragon.")
    async def dragon_praise(self, interaction: discord.Interaction):
        record_contribution(interaction.guild.id, interaction.user, "praise", 2)
        con = connect()
        cur = con.cursor()
        cur.execute("UPDATE dragon SET happiness=MIN(happiness+4,100), bond=MIN(bond+1,100), dragon_message=? WHERE guild_id=?",
                    (f"{interaction.user.display_name} praised me. I feel proud.", interaction.guild.id))
        con.commit()
        con.close()
        await interaction.response.send_message(f"✨ {interaction.user.display_name} praised the dragon. It stands a little taller.")

    @app_commands.command(name="dragon_contributions", description="Show v5 guild dragon contribution leaderboard.")
    async def dragon_contributions(self, interaction: discord.Interaction):
        rows = get_top_contributors(interaction.guild.id)
        if not rows:
            await interaction.response.send_message("No v5 contributions yet.", ephemeral=True)
            return
        lines = [f"**{i}. {username or user_id}** — {total} contribution points" for i, (user_id, username, total) in enumerate(rows, 1)]
        await interaction.response.send_message("🏆 **Guild Dragon Contributions**\n\n" + "\n".join(lines))

    @app_commands.command(name="dragon_memories_v5", description="Show important v5 dragon memories.")
    async def dragon_memories_v5(self, interaction: discord.Interaction):
        rows = get_memories(interaction.guild.id)
        if not rows:
            await interaction.response.send_message("📖 No v5 memories yet.", ephemeral=True)
            return
        lines = []
        for text, memory_type, username, created_at in rows:
            who = f" — {username}" if username else ""
            lines.append(f"• **{memory_type}**{who}: {text}")
        await interaction.response.send_message("📖 **Dragon Memories v5**\n\n" + "\n".join(lines), ephemeral=True)

    @app_commands.command(name="dragon_lair_v5", description="Show or upgrade the v5 dragon lair.")
    @app_commands.describe(room="Optional room to upgrade: nest, crystals, treasure, library, training, forge")
    async def dragon_lair_v5(self, interaction: discord.Interaction, room: str = None):
        if room:
            room_name = upgrade_lair_room(interaction.guild.id, room)
            if not room_name:
                await interaction.response.send_message("Unknown room. Use: nest, crystals, treasure, library, training, forge.", ephemeral=True)
                return
            record_contribution(interaction.guild.id, interaction.user, "lair_upgrade", 3)
            await interaction.response.send_message(f"🏰 {interaction.user.display_name} upgraded **{room_name}**.")
            return

        rows = get_lair(interaction.guild.id)
        if not rows:
            await interaction.response.send_message("🏰 No v5 lair rooms upgraded yet. Try `/dragon_lair_v5 room:nest`.", ephemeral=True)
            return
        lines = [f"• **{name}** — Level {level}" for name, level in rows]
        await interaction.response.send_message("🏰 **Dragon Lair v5**\n\n" + "\n".join(lines), ephemeral=True)

    @app_commands.command(name="dragon_world_event", description="Trigger a v5 dragon world event.")
    async def dragon_world_event(self, interaction: discord.Interaction):
        name, text, reward = create_world_event(interaction.guild.id)
        embed = discord.Embed(title=f"🌍 {name}", description=text, color=0x4da3ff)
        embed.add_field(name="Result", value=reward, inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(V5Cog(bot))
