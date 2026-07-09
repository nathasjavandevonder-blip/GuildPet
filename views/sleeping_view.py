import discord

from embeds import make_dragon_embed
from v5_systems import (
    handle_sleep_interaction,
    talk_response,
    record_contribution,
    get_memories,
)


class SleepingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def refresh(self, interaction: discord.Interaction, msg: str = None):
        from views.state_view import get_state_view

        embed, file = make_dragon_embed(interaction.guild.id)
        view = get_state_view(interaction.guild.id)

        if file:
            await interaction.response.edit_message(embed=embed, attachments=[file], view=view)
        else:
            await interaction.response.edit_message(embed=embed, attachments=[], view=view)

        if msg:
            await interaction.followup.send(msg, ephemeral=True)

    @discord.ui.button(label="Wake Gently", emoji="☕", style=discord.ButtonStyle.success, custom_id="sleep_wake_gently")
    async def wake_gently(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok, msg = handle_sleep_interaction(interaction.guild.id, interaction.user, "wake_gently")
        await self.refresh(interaction, msg)

    @discord.ui.button(label="Whisper", emoji="🤫", style=discord.ButtonStyle.secondary, custom_id="sleep_whisper")
    async def whisper(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok, msg = handle_sleep_interaction(interaction.guild.id, interaction.user, "whisper")
        await self.refresh(interaction, msg)

    @discord.ui.button(label="Cuddle", emoji="💖", style=discord.ButtonStyle.secondary, custom_id="sleep_cuddle")
    async def cuddle(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok, msg = handle_sleep_interaction(interaction.guild.id, interaction.user, "cuddle")
        await self.refresh(interaction, msg)

    @discord.ui.button(label="Let Sleep", emoji="🌙", style=discord.ButtonStyle.secondary, custom_id="sleep_let_sleep")
    async def let_sleep(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok, msg = handle_sleep_interaction(interaction.guild.id, interaction.user, "let_sleep")
        await self.refresh(interaction, msg)

    @discord.ui.button(label="Talk", emoji="💬", style=discord.ButtonStyle.secondary, custom_id="sleep_talk")
    async def talk(self, interaction: discord.Interaction, button: discord.ui.Button):
        text, mood, personality, personal_bond = talk_response(interaction.guild.id, interaction.user)
        record_contribution(interaction.guild.id, interaction.user, "sleep_talk", 1)

        await interaction.response.send_message(
            f"💤 **Sleepy Dragon**\n\n{text}\n\n"
            f"**Mood:** {mood}\n"
            f"**Personality:** {personality}\n"
            f"**Your bond:** {personal_bond}",
            ephemeral=True,
        )

    @discord.ui.button(label="Memories", emoji="📖", style=discord.ButtonStyle.secondary, custom_id="sleep_memories")
    async def memories(self, interaction: discord.Interaction, button: discord.ui.Button):
        rows = get_memories(interaction.guild.id, 8)

        if not rows:
            await interaction.response.send_message("📖 The dragon has no v5 memories yet.", ephemeral=True)
            return

        lines = []
        for text, memory_type, username, created_at in rows:
            who = f" — {username}" if username else ""
            lines.append(f"• **{memory_type}**{who}: {text}")

        await interaction.response.send_message(
            "📖 **Dragon Memories**\n\n" + "\n".join(lines),
            ephemeral=True,
        )
