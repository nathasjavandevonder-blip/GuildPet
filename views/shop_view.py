import discord
from shop import SHOP, buy_item
from embeds import make_shop_embed
from views.updater import update_dragon_message

class ShopSelect(discord.ui.Select):
    def __init__(self):
        options = []
        for key, item in SHOP.items():
            options.append(discord.SelectOption(label=item["name"], value=key, description=f"{item['cost']} guild tokens"))
        super().__init__(placeholder="Choose an upgrade to buy...", options=options)

    async def callback(self, interaction: discord.Interaction):
        ok, msg = buy_item(interaction.guild.id, self.values[0])
        await interaction.response.edit_message(embed=make_shop_embed(interaction.guild.id), view=ShopView())
        await interaction.followup.send(msg, ephemeral=True)
        await update_dragon_message(interaction.guild)

class ShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(ShopSelect())
