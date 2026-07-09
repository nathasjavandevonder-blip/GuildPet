import discord
from rpg import LAIR_UPGRADES, upgrade_lair
from embeds import make_lair_embed
from views.updater import update_dragon_message

class LairUpgradeSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=data["name"], value=key, emoji=data["emoji"], description=data["bonus"][:90]) for key, data in LAIR_UPGRADES.items()]
        super().__init__(placeholder="Choose a lair upgrade...", options=options)

    async def callback(self, interaction: discord.Interaction):
        ok, msg = upgrade_lair(interaction.guild.id, self.values[0])
        await interaction.response.edit_message(embed=make_lair_embed(interaction.guild.id), view=LairView())
        await interaction.followup.send(msg, ephemeral=True)
        await update_dragon_message(interaction.guild)

class LairView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(LairUpgradeSelect())
