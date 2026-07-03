import random
from database import connect, get_dragon
from memories import add_memory

TRAITS = {
    "Brave": {
        "description": "More likely to enjoy training and guarding the lair.",
        "quotes": [
            "I will protect this guild.",
            "Nothing scary gets past me.",
            "One day my roar will shake the sky.",
        ],
    },
    "Curious": {
        "description": "More likely to notice small details and explore.",
        "quotes": [
            "What is behind that rock?",
            "I found something strange near the cave.",
            "I want to explore a little further.",
        ],
    },
    "Gentle": {
        "description": "More affectionate and calm.",
        "quotes": [
            "Stay a little longer.",
            "I like peaceful days with the guild.",
            "You make the lair feel safe.",
        ],
    },
    "Playful": {
        "description": "More energetic and playful.",
        "quotes": [
            "Again! Again!",
            "Can we play now?",
            "I chased my own tail today.",
        ],
    },
    "Lazy": {
        "description": "Sleeps more often and likes resting.",
        "quotes": [
            "Five more minutes...",
            "The nest is too comfortable.",
            "I was dreaming about snacks.",
        ],
    },
    "Protective": {
        "description": "Loves guarding the lair and the guild.",
        "quotes": [
            "I am watching over the guild.",
            "The lair is safe with me here.",
            "I heard something outside, but I scared it away.",
        ],
    },
}

def ensure_trait(guild_id: int):
    d = get_dragon(guild_id)

    if d["dragon_trait"] and d["dragon_trait"] != "Unchosen":
        return d["dragon_trait"]

    trait = random.choice(list(TRAITS.keys()))

    con = connect()
    cur = con.cursor()
    cur.execute(
        "UPDATE dragon SET dragon_trait=?, dragon_message=?, last_action_text=? WHERE guild_id=?",
        (
            trait,
            f"I think I am a {trait.lower()} dragon.",
            f"🌟 The dragon discovered its trait: **{trait}**.",
            guild_id,
        )
    )
    con.commit()
    con.close()

    add_memory(guild_id, f"The dragon discovered its trait: {trait}.")
    return trait

def trait_quote(guild_id: int):
    trait = ensure_trait(guild_id)
    return random.choice(TRAITS[trait]["quotes"])

def trait_description(guild_id: int):
    trait = ensure_trait(guild_id)
    return trait, TRAITS[trait]["description"]
