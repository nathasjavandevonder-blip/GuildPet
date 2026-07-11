from pathlib import Path

path = Path("systems/combat/service.py")
text = path.read_text(encoding="utf-8")

if "from core.events.bus import event_bus" not in text:
    text = text.replace(
        "from core.database import db_session\n",
        "from core.database import db_session\n"
        "from core.events.bus import event_bus\n",
        1,
    )

# perform_action moet async worden omdat publish async is.
text = text.replace(
    "def perform_action(\n",
    "async def perform_action(\n",
    1,
)

victory_marker = '''        reset_to_idle(
            guild_id,
            reason="combat_victory",
        )
'''

recovering_marker = '''        set_state(
            guild_id,
            DragonState.RECOVERING,
'''

if victory_marker in text:
    event_code = '''        await event_bus.emit(
            "combat.won",
            guild_id=guild_id,
            actor_user_id=user_id,
            actor_username=username,
            payload={
                "combat_id": int(combat["id"]),
                "enemy_key": enemy.key,
                "enemy_name": enemy.name,
                "xp": xp_reward,
                "tokens": token_reward,
                "loot": loot,
                "achievements": unlocked,
                "dragon_hp": dragon_hp,
            },
            source="systems.combat.service",
        )

'''
    text = text.replace(
        victory_marker,
        event_code + victory_marker,
        1,
    )

elif recovering_marker in text:
    event_code = '''        await event_bus.emit(
            "combat.won",
            guild_id=guild_id,
            actor_user_id=user_id,
            actor_username=username,
            payload={
                "combat_id": int(combat["id"]),
                "enemy_key": enemy.key,
                "enemy_name": enemy.name,
                "xp": xp_reward,
                "tokens": token_reward,
                "loot": loot,
                "achievements": unlocked,
                "dragon_hp": dragon_hp,
            },
            source="systems.combat.service",
        )

'''
    text = text.replace(
        recovering_marker,
        event_code + recovering_marker,
        1,
    )

else:
    raise SystemExit(
        "Could not locate victory state block."
    )

path.write_text(
    text,
    encoding="utf-8",
)

print("Added Combat Event Bus emissions.")
