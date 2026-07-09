import discord
from rpg import claim_completed_quests
from embeds import make_quests_embed
from views.updater import update_dragon_message

class QuestView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.button(label="Claim Ready Rewards", emoji="🎁", style=discord.ButtonStyle.success)
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        rewards = claim_completed_quests(interaction.guild.id)
        await interaction.response.edit_message(embed=make_quests_embed(interaction.guild.id), view=QuestView())
        await interaction.followup.send("No completed quests to claim yet." if not rewards else "🎁 **Quest rewards claimed**\n" + "\n".join(rewards), ephemeral=True)
        await update_dragon_message(interaction.guild)
