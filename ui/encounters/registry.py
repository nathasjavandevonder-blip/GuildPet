from __future__ import annotations

from collections.abc import Callable

import discord

from ui.encounters.models import EncounterContext


EncounterResult = tuple[
    discord.Embed,
    discord.ui.View | None,
]

EncounterHandler = Callable[
    [EncounterContext, discord.Embed],
    EncounterResult,
]

_HANDLERS: dict[str, EncounterHandler] = {}


def register_handler(
    encounter_key: str,
    handler: EncounterHandler,
) -> None:
    _HANDLERS[encounter_key] = handler


def build_encounter(
    context: EncounterContext,
    embed: discord.Embed,
) -> EncounterResult:
    handler = _HANDLERS.get(context.encounter_key)

    if handler is not None:
        return handler(context, embed)

    titles = {
        "nothing": "🌿 Peaceful Arrival",
        "combat": "⚔️ Danger Nearby",
        "npc": "🧙 Someone Is Waiting",
        "rare": "✨ Rare Discovery",
    }

    descriptions = {
        "nothing": "The area appears peaceful.",
        "combat": "Something dangerous is moving nearby.",
        "npc": "A mysterious figure is waiting beside the path.",
        "rare": "The air feels strange and unusually powerful.",
    }

    embed.add_field(
        name=titles.get(
            context.encounter_key,
            "❓ Something Happened",
        ),
        value=descriptions.get(
            context.encounter_key,
            "The dragon looks around curiously.",
        ),
        inline=False,
    )

    return embed, None
