from __future__ import annotations

import random

from systems.living.personality import dominant_personality
from systems.living.service import get_living_state
from systems.world.dialogue import world_dialogue
from systems.relationships.service import (
    get_relationship,
    relationship_title,
)


MOOD_LINES = {
    "happy": (
        "Today feels like a wonderful day.",
        "I am happy the guild is here.",
    ),
    "excited": (
        "Can we do something exciting?",
        "I feel like I could fly across the whole kingdom!",
    ),
    "content": (
        "It is peaceful here.",
        "I like spending time in our lair.",
    ),
    "hungry": (
        "My stomach is rumbling...",
        "Do we have anything tasty?",
    ),
    "sleepy": (
        "I could really use a nap.",
        "My wings feel heavy...",
    ),
    "lonely": (
        "I missed everyone.",
        "Could someone stay with me for a while?",
    ),
    "dirty": (
        "I think I have dust between my scales.",
        "The lair could use some cleaning.",
    ),
    "grumpy": (
        "Hmph...",
        "I am not in the best mood right now.",
    ),
}


PERSONALITY_LINES = {
    "friendly": (
        "This guild feels like my family.",
        "I like meeting all the keepers.",
    ),
    "brave": (
        "I will protect this guild.",
        "No enemy will frighten me.",
    ),
    "curious": (
        "I wonder what lies beyond the mountains.",
        "Do you think there are hidden caves nearby?",
    ),
    "playful": (
        "Can we play?",
        "I nearly caught my own tail earlier.",
    ),
    "gentle": (
        "Quiet moments are important too.",
        "I feel safe when everyone is kind.",
    ),
    "protective": (
        "I am watching over the lair.",
        "The guild is safe while I am here.",
    ),
    "lazy": (
        "Five more minutes...",
        "The nest is especially comfortable today.",
    ),
    "mischievous": (
        "I may have hidden something shiny.",
        "I definitely did not move the treasure pile.",
    ),
}


def dragon_talk(
    guild_id: int,
    *,
    user_id: int,
    username: str,
) -> str:
    living = get_living_state(guild_id)
    personality = dominant_personality(guild_id)
    relationship = get_relationship(guild_id, user_id)
    title = relationship_title(guild_id, user_id)

    lines = [
        f"**Mood:** {living.mood.value.title()}",
        f"**Personality:** {personality.title()}",
        f"**Your relationship:** {title}",
        "",
        random.choice(
            MOOD_LINES.get(
                living.mood.value,
                MOOD_LINES["content"],
            )
        ),
        random.choice(
            PERSONALITY_LINES.get(
                personality,
                PERSONALITY_LINES["curious"],
            )
        ),
    ]

    if relationship is not None:
        bond = int(relationship["bond"])

        if bond >= 250:
            lines.append(
                f"I always recognize you, {username}. "
                "You are one of my favorite keepers."
            )
        elif bond >= 100:
            lines.append(
                f"It is good to see you again, {username}."
            )
        elif bond >= 25:
            lines.append(
                f"I am starting to know you well, {username}."
            )

    lines.extend([
        "",
        world_dialogue(guild_id),
    ])

    return "\n".join(lines)
