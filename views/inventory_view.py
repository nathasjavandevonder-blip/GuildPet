import discord
from rpg import equip_best_items
from embeds import make_inventory_embed, make_lair_embed
from views.updater import update_dragon_message

class InventoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.button(label="Auto Equip Best", emoji="🛡️", style=discord.ButtonStyle.success)
    async def auto_equip(self, interaction: discord.Interaction, button: discord.ui.Button):
        equipped = equip_best_items(interaction.guild.id)
        msg = "No equipment found in inventory." if not equipped else "\n".join(equipped)
        await interaction.response.edit_message(embed=make_inventory_embed(interaction.guild.id), view=InventoryView())
        await interaction.followup.send(msg, ephemeral=True)
        await update_dragon_message(interaction.guild)

    @discord.ui.button(label="View Lair", emoji="🏡", style=discord.ButtonStyle.secondary)
    async def lair(self, interaction: discord.Interaction, button: discord.ui.Button):
        from views.lair_view import LairView
        await interaction.response.edit_message(embed=make_lair_embed(interaction.guild.id), view=LairView())
