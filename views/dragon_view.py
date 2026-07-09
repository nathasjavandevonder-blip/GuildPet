import discord

from dragon import check_cooldown, apply_action
from achievements import check_achievements, ACHIEVEMENTS
from embeds import make_dragon_embed, make_shop_embed, make_profile_embed, make_research_embed, make_inventory_embed, make_quests_embed, make_lair_embed
from memories import get_memories
from adventures import make_adventure_embed
from views.shop_view import ShopView
from views.research_view import ResearchView
from views.adventure_view import AdventureView
from database import get_dragon
from v5_systems import talk_response, record_contribution, handle_sleep_interaction
from views.inventory_view import InventoryView
from views.quest_view import QuestView
from views.lair_view import LairView


class DragonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def handle(self, interaction: discord.Interaction, action: str):
        ok, mins = check_cooldown(interaction.guild.id, interaction.user.id, action, 30)
        if not ok:
            await interaction.response.send_message(
                f"⏳ You can use **{action}** again in **{mins} minutes**.",
                ephemeral=True,
            )
            return

        apply_action(interaction.guild.id, interaction.user, action)
        unlocked = check_achievements(interaction.guild, interaction.user.id)
        embed, file = make_dragon_embed(interaction.guild.id)

        if file:
            await interaction.response.edit_message(embed=embed, attachments=[file], view=__import__('views.state_view', fromlist=['get_state_view']).get_state_view(interaction.guild.id))
        else:
            await interaction.response.edit_message(embed=embed, attachments=[], view=__import__('views.state_view', fromlist=['get_state_view']).get_state_view(interaction.guild.id))

        if unlocked:
            lines = [f"{ACHIEVEMENTS[key][0]} — {ACHIEVEMENTS[key][1]}" for key in unlocked]
            await interaction.followup.send(
                "🏆 **Achievement unlocked!**\n" + "\n".join(lines),
                ephemeral=True,
            )

    @discord.ui.button(label="Feed", emoji="🍖", style=discord.ButtonStyle.danger, custom_id="dragon_feed")
    async def feed(self, interaction, button):
        await self.handle(interaction, "feed")

    @discord.ui.button(label="Play", emoji="🟢", style=discord.ButtonStyle.success, custom_id="dragon_play")
    async def play(self, interaction, button):
        await self.handle(interaction, "play")

    @discord.ui.button(label="Train", emoji="🏋️", style=discord.ButtonStyle.primary, custom_id="dragon_train")
    async def train(self, interaction, button):
        await self.handle(interaction, "train")

    @discord.ui.button(label="Clean", emoji="🛁", style=discord.ButtonStyle.secondary, custom_id="dragon_clean")
    async def clean(self, interaction, button):
        await self.handle(interaction, "clean")

    @discord.ui.button(label="Rest", emoji="😴", style=discord.ButtonStyle.secondary, custom_id="dragon_rest")
    async def rest(self, interaction, button):
        await self.handle(interaction, "rest")

    @discord.ui.button(label="Bond", emoji="❤️", style=discord.ButtonStyle.success, custom_id="dragon_bond")
    async def bond(self, interaction, button):
        await self.handle(interaction, "bond")

    @discord.ui.button(label="Shop", emoji="🛒", style=discord.ButtonStyle.primary, custom_id="dragon_shop")
    async def shop(self, interaction, button):
        await interaction.response.send_message(
            embed=make_shop_embed(interaction.guild.id),
            view=ShopView(),
            ephemeral=True,
        )

    @discord.ui.button(label="Research", emoji="📚", style=discord.ButtonStyle.primary, custom_id="dragon_research_button")
    async def research(self, interaction, button):
        await interaction.response.send_message(
            embed=make_research_embed(interaction.guild.id),
            view=ResearchView(),
            ephemeral=True,
        )

    @discord.ui.button(label="Adventure", emoji="🗺️", style=discord.ButtonStyle.primary, custom_id="dragon_adventure_button")
    async def adventure(self, interaction, button):
        await interaction.response.send_message(
            embed=make_adventure_embed(interaction.guild.id),
            view=AdventureView(),
            ephemeral=True,
        )


    @discord.ui.button(label="Inventory", emoji="🎒", style=discord.ButtonStyle.success, custom_id="dragon_inventory_button")
    async def inventory(self, interaction, button):
        await interaction.response.send_message(embed=make_inventory_embed(interaction.guild.id), view=InventoryView(), ephemeral=True)

    @discord.ui.button(label="Quests", emoji="📜", style=discord.ButtonStyle.success, custom_id="dragon_quests_button")
    async def quests(self, interaction, button):
        await interaction.response.send_message(embed=make_quests_embed(interaction.guild.id), view=QuestView(), ephemeral=True)

    @discord.ui.button(label="Lair", emoji="🏡", style=discord.ButtonStyle.secondary, custom_id="dragon_lair_button")
    async def lair(self, interaction, button):
        await interaction.response.send_message(embed=make_lair_embed(interaction.guild.id), view=LairView(), ephemeral=True)

    @discord.ui.button(label="Leaderboard", emoji="🏆", style=discord.ButtonStyle.primary, custom_id="dragon_leaderboard")
    async def leaderboard(self, interaction, button):
        from database import connect

        con = connect()
        cur = con.cursor()
        cur.execute(
            "SELECT user_id, points, tokens, keeper_title FROM players WHERE guild_id=? ORDER BY points DESC LIMIT 10",
            (interaction.guild.id,),
        )
        rows = cur.fetchall()
        con.close()

        if not rows:
            await interaction.response.send_message("No leaderboard yet.", ephemeral=True)
            return

        lines = []
        for i, (user_id, points, tokens, title) in enumerate(rows, start=1):
            member = interaction.guild.get_member(user_id)
            if not member:
                try:
                    member = await interaction.guild.fetch_member(user_id)
                except Exception:
                    member = None

            name = member.display_name if member else f"User {user_id}"
            title = title or "Dragon Keeper"
            lines.append(f"**{i}. {name}** — *{title}*\n{points} points | {tokens} tokens")

        await interaction.response.send_message(
            "🏆 **Top Dragon Keepers**\n\n" + "\n\n".join(lines),
            ephemeral=True,
        )

    @discord.ui.button(label="Profile", emoji="🎖️", style=discord.ButtonStyle.secondary, custom_id="dragon_profile_button")
    async def profile(self, interaction, button):
        await interaction.response.send_message(
            embed=make_profile_embed(interaction.guild, interaction.user),
            ephemeral=True,
        )

    @discord.ui.button(label="Talk", emoji="💬", style=discord.ButtonStyle.secondary, custom_id="dragon_v5_talk")
    async def v5_talk(self, interaction, button):
        text, mood, personality, personal_bond = talk_response(interaction.guild.id, interaction.user)
        record_contribution(interaction.guild.id, interaction.user, "talk", 1)
        await interaction.response.send_message(
            f"💬 **The dragon speaks**\n\n{text}\n\n**Mood:** {mood}\n**Personality:** {personality}\n**Your bond:** {personal_bond}",
            ephemeral=True,
        )

    @discord.ui.button(label="Memories", emoji="📖", style=discord.ButtonStyle.secondary, custom_id="dragon_memories")
    async def memories(self, interaction, button):
        rows = get_memories(interaction.guild.id)
        if not rows:
            await interaction.response.send_message("📖 No dragon memories yet.", ephemeral=True)
            return

        lines = [f"• {text}" for text, _ in rows]
        await interaction.response.send_message(
            "📖 **Dragon Memories**\n\n" + "\n".join(lines),
            ephemeral=True,
        )
