from __future__ import annotations

import discord

from systems.onboarding.service import (
    EGGS,
    cast_vote,
    egg_care_breakdown,
    egg_care_count,
    recent_diary,
    register_egg_care,
    register_hatchling_care,
    resolve_lifecycle,
    total_votes,
    vote_counts,
)


def _progress_bar(value: int, target: int, width: int = 10) -> str:
    if target <= 0:
        return "█" * width
    filled = min(width, int((value / target) * width))
    return "█" * filled + "░" * (width - filled)


def build_egg_embed(guild_id: int) -> discord.Embed:
    lifecycle = resolve_lifecycle(guild_id)
    if lifecycle.stage == "egg_vote":
        counts = vote_counts(guild_id)
        lines = []
        for key, (name, flavour, influence) in EGGS.items():
            lines.append(
                f"**{name}** — {counts[key]} vote(s)\n"
                f"*{flavour}*\n"
                f"Possible influence: {influence}"
            )
        embed = discord.Embed(
            title="🥚 Choose Your Guild's Egg",
            description=(
                "Every member may cast one vote and may change it until voting closes.\n\n"
                "**Important:** the egg does **not** determine the dragon's colour, species, "
                "or artwork. It influences personality, talents, strengths, and development.**\n\n"
                + "\n\n".join(lines)
            ),
            color=discord.Color.gold(),
        )
        embed.add_field(name="Total votes", value=str(total_votes(guild_id)), inline=True)
        if lifecycle.vote_ends_at:
            embed.add_field(
                name="Voting closes",
                value=f"<t:{int(lifecycle.vote_ends_at.timestamp())}:R>",
                inline=True,
            )
        embed.set_footer(text="One member, one vote. Changing your choice moves your vote.")
        return embed

    if lifecycle.stage == "incubating":
        egg_name = EGGS.get(lifecycle.selected_egg or "", ("Mysterious Egg", "", ""))[0]
        care = egg_care_count(guild_id)
        target = lifecycle.egg_care_required
        breakdown = egg_care_breakdown(guild_id)
        embed = discord.Embed(
            title=f"🥚 {egg_name}",
            description=(
                "The guild has chosen its egg. It cannot travel, fight, use equipment, "
                "or go on adventures. For now, everyone can only protect and care for it.\n\n"
                "Each member may perform **one egg-care action per day**."
            ),
            color=discord.Color.teal(),
        )
        embed.add_field(
            name="Guild care",
            value=f"`{_progress_bar(care, target)}` **{care}/{target}** minimum care actions",
            inline=False,
        )
        embed.add_field(
            name="Care given",
            value=(
                f"🤗 {breakdown['cuddle']}  🔥 {breakdown['warm']}  🎵 {breakdown['sing']}\n"
                f"📖 {breakdown['story']}  🛡️ {breakdown['guard']}"
            ),
            inline=False,
        )
        if lifecycle.hatch_at:
            if care < target:
                timing = (
                    f"The shell can begin opening <t:{int(lifecycle.hatch_at.timestamp())}:R>, "
                    f"after the guild has given at least **{target}** care actions."
                )
            else:
                timing = f"Expected hatch: <t:{int(lifecycle.hatch_at.timestamp())}:R>"
            embed.add_field(name="Hatching", value=timing, inline=False)
        diary = recent_diary(guild_id, 1)
        if diary:
            embed.add_field(name="Latest feeling", value=f"*{diary[0]['entry_text']}*", inline=False)
        return embed

    return build_hatchling_embed(guild_id)


def build_hatchling_embed(guild_id: int) -> discord.Embed:
    embed = discord.Embed(
        title="🐣 Your Dragon Has Hatched",
        description=(
            "The dragon is still very young. Feed it, play with it, help it rest, tell stories, "
            "and build a bond together.\n\n"
            "**Travel, combat, inventory, and equipment are still locked.** They will unlock "
            "naturally when the dragon is old and ready enough."
        ),
        color=discord.Color.green(),
    )
    diary = recent_diary(guild_id, 3)
    if diary:
        embed.add_field(
            name="📖 Dragon Diary",
            value="\n".join(f"• *{row['entry_text']}*" for row in diary),
            inline=False,
        )
    embed.set_footer(text="The game grows together with the dragon.")
    return embed


class EggVoteView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        emojis = {
            "crimson": "❤️", "azure": "💙", "emerald": "💚",
            "ivory": "🤍", "shadow": "💜", "golden": "💛",
        }
        for index, (key, (name, _, _)) in enumerate(EGGS.items()):
            button = discord.ui.Button(
                label=name.replace(" Egg", ""),
                emoji=emojis[key],
                style=discord.ButtonStyle.secondary,
                custom_id=f"v55_egg_vote_{key}",
                row=0 if index < 3 else 1,
            )

            async def callback(interaction: discord.Interaction, egg_key=key):
                if interaction.user.bot:
                    return
                try:
                    cast_vote(interaction.guild_id, interaction.user.id, egg_key)
                except ValueError as exc:
                    await interaction.response.send_message(str(exc), ephemeral=True, delete_after=30)
                    return
                await interaction.response.edit_message(
                    embed=build_egg_embed(interaction.guild_id),
                    view=EggVoteView(interaction.guild_id),
                )

            button.callback = callback
            self.add_item(button)


class EggCareView(discord.ui.View):
    ACTIONS = (
        ("Cuddle", "🤗", "cuddle"),
        ("Keep Warm", "🔥", "warm"),
        ("Sing", "🎵", "sing"),
        ("Tell Story", "📖", "story"),
        ("Guard", "🛡️", "guard"),
    )

    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        for label, emoji, action in self.ACTIONS:
            button = discord.ui.Button(
                label=label,
                emoji=emoji,
                style=discord.ButtonStyle.secondary,
                custom_id=f"v55_egg_care_{action}",
            )

            async def callback(interaction: discord.Interaction, action_key=action):
                try:
                    accepted = register_egg_care(
                        interaction.guild_id,
                        interaction.user.id,
                        action_key,
                    )
                except ValueError as exc:
                    await interaction.response.send_message(str(exc), ephemeral=True, delete_after=30)
                    return
                if not accepted:
                    await interaction.response.send_message(
                        "You already cared for the egg today. Come back tomorrow.",
                        ephemeral=True,
                        delete_after=30,
                    )
                    return
                await interaction.response.edit_message(
                    embed=build_egg_embed(interaction.guild_id),
                    view=EggCareView(interaction.guild_id),
                )

            button.callback = callback
            self.add_item(button)


class HatchlingCareView(discord.ui.View):
    ACTIONS = (
        ("Feed", "🍖", "feed"),
        ("Play", "🧸", "play"),
        ("Rest", "😴", "rest"),
        ("Bond", "❤️", "bond"),
        ("Story", "📖", "story"),
    )

    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        for label, emoji, action in self.ACTIONS:
            button = discord.ui.Button(
                label=label,
                emoji=emoji,
                style=discord.ButtonStyle.secondary,
                custom_id=f"v55_hatchling_care_{action}",
            )

            async def callback(interaction: discord.Interaction, action_key=action):
                try:
                    accepted = register_hatchling_care(
                        interaction.guild_id,
                        interaction.user.id,
                        action_key,
                    )
                except ValueError as exc:
                    await interaction.response.send_message(str(exc), ephemeral=True, delete_after=30)
                    return
                text = (
                    "The hatchling reacts happily to your care."
                    if accepted
                    else "You already cared for the hatchling today. Come back tomorrow."
                )
                await interaction.response.send_message(
                    f"🐣 {text}",
                    ephemeral=True,
                    delete_after=30,
                )

            button.callback = callback
            self.add_item(button)
