import discord
from progression import RESEARCH, buy_research
from embeds import make_research_embed
from views.updater import update_dragon_message

class ResearchSelect(discord.ui.Select):
    def __init__(self):
        options = []
        for key, item in RESEARCH.items():
            options.append(discord.SelectOption(
                label=item["name"],
                value=key,
                description=f"{item['cost']} research points"
            ))
        super().__init__(placeholder="Choose research to unlock...", options=options)

    async def callback(self, interaction: discord.Interaction):
        ok, msg = buy_research(interaction.guild.id, self.values[0])
        await interaction.response.edit_message(embed=make_research_embed(interaction.guild.id), view=ResearchView())
        await interaction.followup.send(msg, ephemeral=True)
        await update_dragon_message(interaction.guild)

class ResearchView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(ResearchSelect())
