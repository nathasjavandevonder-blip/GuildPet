import discord
from adventures import ADVENTURES, start_adventure, claim_adventure, make_adventure_embed
from views.updater import update_dragon_message

class AdventureSelect(discord.ui.Select):
    def __init__(self):
        options=[discord.SelectOption(label=adv["name"],value=key,emoji=adv["emoji"],description=f"{adv['minutes']} min · {adv['energy_cost']} energy · {adv['min_xp']} XP req") for key,adv in ADVENTURES.items()]
        super().__init__(placeholder="Choose an adventure route...",options=options,custom_id="adventure_select_route")
    async def callback(self, interaction: discord.Interaction):
        ok,msg=start_adventure(interaction.guild.id,interaction.user.id,self.values[0])
        await interaction.response.edit_message(embed=make_adventure_embed(interaction.guild.id),view=AdventureView())
        await interaction.followup.send(msg,ephemeral=True)
        await update_dragon_message(interaction.guild)
class AdventureView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180); self.add_item(AdventureSelect())
    @discord.ui.button(label="Claim Return",emoji="🎒",style=discord.ButtonStyle.success,custom_id="adventure_claim_return")
    async def claim(self,interaction:discord.Interaction,button:discord.ui.Button):
        ok,msg=claim_adventure(interaction.guild.id,interaction.user)
        await interaction.response.edit_message(embed=make_adventure_embed(interaction.guild.id),view=AdventureView())
        await interaction.followup.send(msg,ephemeral=True)
        await update_dragon_message(interaction.guild)
    @discord.ui.button(label="Refresh",emoji="🔄",style=discord.ButtonStyle.secondary,custom_id="adventure_refresh")
    async def refresh(self,interaction:discord.Interaction,button:discord.ui.Button):
        await interaction.response.edit_message(embed=make_adventure_embed(interaction.guild.id),view=AdventureView())
