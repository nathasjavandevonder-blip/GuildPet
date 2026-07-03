import discord
from events import claim_event
from achievements import check_achievements, ACHIEVEMENTS
from views.updater import update_dragon_message

class EventView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim Event", emoji="🎁", style=discord.ButtonStyle.success, custom_id="dragon_event_claim")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok, msg = claim_event(interaction.guild.id, interaction.user)
        if not ok:
            await interaction.response.send_message(msg, ephemeral=True)
            return
        unlocked = check_achievements(interaction.guild, interaction.user.id)
        await interaction.response.edit_message(content=msg, embed=None, view=None)
        await update_dragon_message(interaction.guild)
        if unlocked:
            lines = [f"{ACHIEVEMENTS[key][0]} — {ACHIEVEMENTS[key][1]}" for key in unlocked]
            await interaction.followup.send("🏅 **Achievement unlocked!**\n" + "\n".join(lines), ephemeral=True)
