from __future__ import annotations

import discord

from systems.living.service import get_living_state
from systems.state.models import DragonState
from systems.state.service import resolve_expired_state


STATE_NAMES = {
    DragonState.IDLE: "Relaxing",
    DragonState.SLEEPING: "Sleeping",
    DragonState.ADVENTURE: "On Adventure",
    DragonState.COMBAT: "In Combat",
    DragonState.RECOVERING: "Recovering",
    DragonState.CELEBRATING: "Celebrating",
}


def build_main_embed(guild_id: int) -> discord.Embed:
    living = get_living_state(guild_id)
    state = resolve_expired_state(guild_id)

    embed = discord.Embed(
        title="🐉 GuildPet v5 Alpha",
        description=(
            f"**Current state:** {STATE_NAMES[state.state]}\n"
            f"**Activity:** {living.current_activity.title()}\n"
            f"**Mood:** {living.mood.value.title()}"
        ),
        color=discord.Color.blurple(),
    )

    embed.add_field(
        name="🍖 Hunger",
        value=f"**{living.hunger}/100**",
        inline=True,
    )
    embed.add_field(
        name="😊 Happiness",
        value=f"**{living.happiness}/100**",
        inline=True,
    )
    embed.add_field(
        name="⚡ Energy",
        value=f"**{living.energy}/100**",
        inline=True,
    )
    embed.add_field(
        name="🛁 Cleanliness",
        value=f"**{living.cleanliness}/100**",
        inline=True,
    )
    embed.add_field(
        name="❤️ Guild Bond",
        value=f"**{living.bond}/100**",
        inline=True,
    )

    embed.set_footer(
        text=(
            "GuildPet v5 test environment — "
            "this panel is automatically kept at the bottom"
        )
    )

    return embed
