import discord
from dragon import check_cooldown, apply_action
from achievements import check_achievements, ACHIEVEMENTS
from embeds import make_dragon_embed, make_shop_embed, make_profile_embed, make_world_embed
from memories import get_memories
from views.shop_view import ShopView


class DragonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def handle(self, interaction: discord.Interaction, action: str):
        ok, mins = check_cooldown(interaction.guild.id, interaction.user.id, action, 30)

        if not ok:
            await interaction.response.send_message(
                f"⏳ You can use **{action}** again in **{mins} minutes**.",
                ephemeral=True
            )
            return

        apply_action(interaction.guild.id, interaction.user, action)
        unlocked = check_achievements(interaction.guild, interaction.user.id)

        embed, file = make_dragon_embed(interaction.guild.id)

        if file:
            await interaction.response.edit_message(embed=embed, attachments=[file], view=DragonView())
        else:
            await interaction.response.edit_message(embed=embed, attachments=[], view=DragonView())

        if unlocked:
            lines = [f"{ACHIEVEMENTS[key][0]} — {ACHIEVEMENTS[key][1]}" for key in unlocked]
            await interaction.followup.send(
                "🏅 **Achievement unlocked!**\n" + "\n".join(lines),
                ephemeral=True
            )

    @discord.ui.button(label="Feed", emoji="🍖", style=discord.ButtonStyle.danger, custom_id="dragon_feed")
    async def feed(self, interaction, button):
        await self.handle(interaction, "feed")

    @discord.ui.button(label="Play", emoji="🎾", style=discord.ButtonStyle.success, custom_id="dragon_play")
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
            ephemeral=True
        )

    @discord.ui.button(label="World", emoji="🌍", style=discord.ButtonStyle.primary, custom_id="dragon_world_button")
    async def world(self, interaction, button):
        await interaction.response.send_message(
            embed=make_world_embed(interaction.guild.id),
            ephemeral=True
        )

    @discord.ui.button(label="Leaderboard", emoji="🏆", style=discord.ButtonStyle.primary, custom_id="dragon_leaderboard")
    async def leaderboard(self, interaction, button):
        from database import connect

        con = connect()
        cur = con.cursor()
        cur.execute(
            "SELECT user_id, points, tokens, keeper_title FROM players WHERE guild_id=? ORDER BY points DESC LIMIT 10",
            (interaction.guild.id,)
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
            ephemeral=True
        )

    @discord.ui.button(label="Profile", emoji="🎖️", style=discord.ButtonStyle.secondary, custom_id="dragon_profile_button")
    async def profile(self, interaction, button):
        await interaction.response.send_message(
            embed=make_profile_embed(interaction.guild, interaction.user),
            ephemeral=True
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
            ephemeral=True
        )
