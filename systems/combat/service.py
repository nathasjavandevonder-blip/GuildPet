from __future__ import annotations

import json
import random

from core.database import db_session
from systems.achievements.service import add_progress
from systems.combat.catalog import get_enemy
from systems.combat.models import CombatResult
from systems.state.models import DragonState
from systems.state.service import reset_to_idle, set_state


class CombatNotFound(LookupError):
    pass


class CombatFinished(ValueError):
    pass


def start_combat(
    guild_id: int,
    *,
    enemy_key: str = "training_goblin",
    dragon_max_hp: int = 100,
    channel_id: int | None = None,
    message_id: int | None = None,
) -> int:
    enemy = get_enemy(enemy_key)

    with db_session() as connection:
        cursor = connection.execute(
            """
            INSERT INTO combat_sessions (
                guild_id,
                channel_id,
                message_id,
                dragon_hp,
                dragon_max_hp,
                enemy_key,
                enemy_hp,
                enemy_max_hp,
                turn_number,
                status,
                combat_data,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 'active', '{}',
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (
                guild_id,
                channel_id,
                message_id,
                dragon_max_hp,
                dragon_max_hp,
                enemy.key,
                enemy.max_hp,
                enemy.max_hp,
            ),
        )
        combat_id = int(cursor.lastrowid)

    set_state(
        guild_id,
        DragonState.COMBAT,
        payload={"combat_id": combat_id},
        force=True,
    )

    return combat_id


def get_active_combat(guild_id: int):
    with db_session() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM combat_sessions
            WHERE guild_id = ? AND status = 'active'
            ORDER BY id DESC
            LIMIT 1
            """,
            (guild_id,),
        ).fetchone()

    return row


def _enemy_attack(enemy, guarded: bool) -> tuple[int, str]:
    damage = random.randint(
        enemy.attack_min,
        enemy.attack_max,
    )

    if guarded:
        damage = max(1, damage // 2)
        return damage, (
            f"{enemy.emoji} **{enemy.name}** attacks, "
            f"but Guard reduces the damage to **{damage}**."
        )

    return damage, (
        f"{enemy.emoji} **{enemy.name}** attacks for "
        f"**{damage} damage**."
    )


def perform_action(
    guild_id: int,
    *,
    user_id: int,
    username: str,
    action_key: str,
) -> CombatResult:
    combat = get_active_combat(guild_id)

    if combat is None:
        raise CombatNotFound("No active combat found.")

    if combat["status"] != "active":
        raise CombatFinished("This combat has already ended.")

    enemy = get_enemy(combat["enemy_key"])

    dragon_hp = int(combat["dragon_hp"])
    enemy_hp = int(combat["enemy_hp"])
    turn = int(combat["turn_number"])

    guarded = action_key == "guard"
    damage = 0

    if action_key == "attack":
        damage = max(
            1,
            random.randint(9, 16) - enemy.armor,
        )
        action_text = (
            f"🦴 **{username}** orders a bite attack for "
            f"**{damage} damage**."
        )

    elif action_key == "fire_breath":
        base_damage = random.randint(12, 20)
        damage = max(
            1,
            int(base_damage * enemy.fire_weakness) - enemy.armor,
        )
        action_text = (
            f"🔥 **{username}** uses Fire Breath for "
            f"**{damage} damage**."
        )

    elif action_key == "guard":
        action_text = (
            f"🛡️ **{username}** tells the dragon to guard."
        )

    elif action_key == "retreat":
        with db_session() as connection:
            connection.execute(
                """
                UPDATE combat_sessions
                SET status = 'retreated',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (combat["id"],),
            )

        reset_to_idle(
            guild_id,
            reason="combat_retreat",
        )

        return CombatResult(
            combat_id=combat["id"],
            description=(
                f"🏃 **{username}** helped the dragon retreat safely."
            ),
            dragon_hp=dragon_hp,
            dragon_max_hp=combat["dragon_max_hp"],
            enemy_hp=enemy_hp,
            enemy_max_hp=combat["enemy_max_hp"],
            status="retreated",
            turn_number=turn,
        )

    else:
        raise ValueError(f"Unknown combat action: {action_key}")

    enemy_hp = max(enemy_hp - damage, 0)
    log_lines = [action_text]

    if enemy_hp <= 0:
        status = "victory"
        log_lines.append(
            f"🏆 **{enemy.name} was defeated!**"
        )

        with db_session() as connection:
            connection.execute(
                """
                UPDATE combat_sessions
                SET enemy_hp = 0,
                    status = 'victory',
                    turn_number = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    turn,
                    combat["id"],
                ),
            )

        add_progress(
            guild_id,
            user_id,
            "combat_wins",
            1,
        )

        if dragon_hp <= 5:
            add_progress(
                guild_id,
                user_id,
                "low_hp_victories",
                1,
            )

        reset_to_idle(
            guild_id,
            reason="combat_victory",
        )

    else:
        enemy_damage, enemy_text = _enemy_attack(
            enemy,
            guarded,
        )
        dragon_hp = max(dragon_hp - enemy_damage, 0)
        log_lines.append(enemy_text)

        if dragon_hp <= 0:
            status = "defeat"
            log_lines.append(
                "💔 The dragon has been defeated and must recover."
            )

            set_state(
                guild_id,
                DragonState.RECOVERING,
                payload={
                    "reason": "combat_defeat",
                    "combat_id": combat["id"],
                },
                force=True,
            )
        else:
            status = "active"

        with db_session() as connection:
            connection.execute(
                """
                UPDATE combat_sessions
                SET dragon_hp = ?,
                    enemy_hp = ?,
                    status = ?,
                    turn_number = turn_number + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    dragon_hp,
                    enemy_hp,
                    status,
                    combat["id"],
                ),
            )

    with db_session() as connection:
        connection.execute(
            """
            INSERT INTO combat_participants_v5 (
                combat_id,
                user_id,
                username,
                contribution,
                last_action,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT (combat_id, user_id)
            DO UPDATE SET
                username = excluded.username,
                contribution = contribution + excluded.contribution,
                last_action = excluded.last_action,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                combat["id"],
                user_id,
                username,
                damage,
                action_key,
            ),
        )

        connection.execute(
            """
            INSERT INTO combat_actions_v5 (
                combat_id,
                user_id,
                action_key,
                damage,
                description,
                turn_number
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                combat["id"],
                user_id,
                action_key,
                damage,
                "\n".join(log_lines),
                turn,
            ),
        )

    return CombatResult(
        combat_id=combat["id"],
        description="\n".join(log_lines),
        dragon_hp=dragon_hp,
        dragon_max_hp=combat["dragon_max_hp"],
        enemy_hp=enemy_hp,
        enemy_max_hp=combat["enemy_max_hp"],
        status=status,
        turn_number=turn,
    )
