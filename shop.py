from database import db_session, get_dragon, add_memory_tx, execute_with_retry

SHOP = {
    "moss_nest": {"name": "Moss Nest", "cost": 500, "type": "lair", "description": "A soft green nest for the dragon."},
    "crystal_nest": {"name": "Crystal Nest", "cost": 1500, "type": "lair", "description": "A magical nest filled with crystals."},
    "lava_nest": {"name": "Lava Nest", "cost": 1500, "type": "lair", "description": "A warm volcanic nest."},
    "royal_hall": {"name": "Royal Dragon Hall", "cost": 5000, "type": "lair", "description": "A royal room for a legendary dragon."},
    "sky_fortress": {"name": "Sky Fortress", "cost": 15000, "type": "lair", "description": "A fortress above the clouds."},
    "golden_bowl": {"name": "Golden Bowl", "cost": 1000, "type": "upgrade", "description": "Feed gives +5 extra hunger."},
    "training_dummy": {"name": "Training Dummy", "cost": 1200, "type": "upgrade", "description": "Train gives +3 extra XP."},
    "bubble_bath": {"name": "Bubble Bath", "cost": 1000, "type": "upgrade", "description": "Clean gives +5 extra cleanliness."},
}

def has_item(guild_id: int, item_key: str):
    with db_session() as con:
        cur = con.cursor()
        cur.execute(
            "SELECT bought FROM shop_items WHERE guild_id=? AND item_key=?",
            (guild_id, item_key)
        )
        row = cur.fetchone()
        return bool(row and row[0])

def buy_item(guild_id: int, item_key: str):
    def work():
        if item_key not in SHOP:
            return False, "Unknown shop item."

        item = SHOP[item_key]
        d = get_dragon(guild_id)

        with db_session() as con:
            cur = con.cursor()

            cur.execute(
                "SELECT bought FROM shop_items WHERE guild_id=? AND item_key=?",
                (guild_id, item_key)
            )
            already = cur.fetchone()

            if already and already[0]:
                return False, "This upgrade has already been bought."

            if d["guild_tokens"] < item["cost"]:
                return False, f"The guild needs **{item['cost']} Guild Tokens**. Current: **{d['guild_tokens']}**."

            cur.execute(
                "UPDATE dragon SET guild_tokens = guild_tokens - ? WHERE guild_id=?",
                (item["cost"], guild_id)
            )

            cur.execute(
                "INSERT OR REPLACE INTO shop_items (guild_id, item_key, bought) VALUES (?, ?, 1)",
                (guild_id, item_key)
            )

            if item["type"] == "lair":
                cur.execute(
                    "UPDATE dragon SET lair=?, last_action_text=?, dragon_message=? WHERE guild_id=?",
                    (
                        item["name"],
                        f"🏡 The guild unlocked **{item['name']}**!",
                        f"I love my new {item['name']}!",
                        guild_id
                    )
                )
                add_memory_tx(cur, guild_id, f"The guild unlocked the lair upgrade: {item['name']}.")

        return True, f"✅ The guild bought **{item['name']}**!"

    return execute_with_retry(work)
