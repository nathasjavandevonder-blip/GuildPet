import discord
from events import claim_event
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

        await interaction.response.edit_message(content=msg, embed=None, view=None)
        await update_dragon_message(interaction.guild)
