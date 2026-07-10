from __future__ import annotations

import json
import random
from datetime import timedelta

from core.database import db_session
from systems.achievements.service import add_progress
from systems.chronicle.service import add_chronicle_entry
from systems.combat.catalog import get_enemy
from systems.combat.models import CombatResult
from systems.relationships.service import record_relationship_action
from systems.living.service import apply_combat_aftermath
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
    if get_active_combat(guild_id) is not None:
        raise ValueError("The dragon is already in combat.")

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
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, 1, 'active', '{}',
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
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
        return connection.execute(
            """
            SELECT *
            FROM combat_sessions
            WHERE guild_id = ? AND status = 'active'
            ORDER BY id DESC
            LIMIT 1
            """,
            (guild_id,),
        ).fetchone()


def get_combat(combat_id: int):
    with db_session() as connection:
        return connection.execute(
            "SELECT * FROM combat_sessions WHERE id = ?",
            (combat_id,),
        ).fetchone()


def get_recent_actions(
    combat_id: int,
    *,
    limit: int = 4,
):
    with db_session() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM combat_actions_v5
            WHERE combat_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (combat_id, limit),
        ).fetchall()

    return list(reversed(rows))


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


def _roll_loot(enemy) -> list[str]:
    loot: list[str] = []

    for entry in enemy.loot_table:
        chance = float(entry.get("chance", 0))

        if random.random() > chance:
            continue

        minimum = int(entry.get("min_quantity", 1))
        maximum = int(entry.get("max_quantity", minimum))
        quantity = random.randint(minimum, maximum)
        item_key = str(entry["item_key"])

        loot.extend([item_key] * quantity)

    return loot


def _award_victory(
    *,
    combat_id: int,
    guild_id: int,
    user_id: int,
    username: str,
    enemy,
    dragon_hp: int,
) -> tuple[list[str], list[str]]:
    loot = _roll_loot(enemy)
    unlocked: list[str] = []

    unlocked.extend(
        add_progress(
            guild_id,
            user_id,
            "combat_wins",
            1,
        )
    )

    if dragon_hp <= 5:
        unlocked.extend(
            add_progress(
                guild_id,
                user_id,
                "low_hp_victories",
                1,
            )
        )

    with db_session() as connection:
        connection.execute(
            """
            INSERT INTO player_wallet_v5 (
                guild_id,
                user_id,
                username,
                tokens,
                adventure_xp
            )
            VALUES (?, ?, ?, ?, 0)
            ON CONFLICT (guild_id, user_id)
            DO UPDATE SET
                username = excluded.username,
                tokens = tokens + excluded.tokens,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                guild_id,
                user_id,
                username,
                enemy.token_reward,
            ),
        )

        connection.execute(
            """
            INSERT INTO player_combat_progress_v5 (
                guild_id,
                user_id,
                username,
                combat_xp,
                victories
            )
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT (guild_id, user_id)
            DO UPDATE SET
                username = excluded.username,
                combat_xp = combat_xp + excluded.combat_xp,
                victories = victories + 1,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                guild_id,
                user_id,
                username,
                enemy.xp_reward,
            ),
        )

        for item_key in loot:
            connection.execute(
                """
                INSERT INTO player_items_v5 (
                    guild_id,
                    user_id,
                    item_key,
                    quantity
                )
                VALUES (?, ?, ?, 1)
                ON CONFLICT (guild_id, user_id, item_key)
                DO UPDATE SET
                    quantity = quantity + 1,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    guild_id,
                    user_id,
                    item_key,
                ),
            )

        connection.execute(
            """
            INSERT INTO combat_rewards_v5 (
                combat_id,
                guild_id,
                user_id,
                username,
                xp,
                tokens,
                loot_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                combat_id,
                guild_id,
                user_id,
                username,
                enemy.xp_reward,
                enemy.token_reward,
                json.dumps(loot),
            ),
        )

        connection.execute(
            """
            UPDATE combat_sessions
            SET combat_data = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                json.dumps(
                    {
                        "winner_user_id": user_id,
                        "winner_username": username,
                        "xp_reward": enemy.xp_reward,
                        "token_reward": enemy.token_reward,
                        "loot": loot,
                        "achievements": list(dict.fromkeys(unlocked)),
                    }
                ),
                combat_id,
            ),
        )

    record_relationship_action(
        guild_id,
        user_id,
        username,
        "combat",
    )

    add_chronicle_entry(
        guild_id,
        entry_type="combat_victory",
        title=f"Victory over {enemy.name}",
        description=(
            f"{username} guided the dragon to victory and earned "
            f"{enemy.xp_reward} XP and {enemy.token_reward} tokens."
        ),
        importance=2,
        metadata={
            "combat_id": combat_id,
            "enemy_key": enemy.key,
            "loot": loot,
        },
    )

    return loot, list(dict.fromkeys(unlocked))


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

    enemy = get_enemy(combat["enemy_key"])

    dragon_hp = int(combat["dragon_hp"])
    enemy_hp = int(combat["enemy_hp"])
    turn = int(combat["turn_number"])

    guarded = action_key == "guard"
    damage = 0
    loot: list[str] = []
    unlocked: list[str] = []
    xp_reward = 0
    token_reward = 0

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

            connection.execute(
                """
                INSERT INTO player_combat_progress_v5 (
                    guild_id,
                    user_id,
                    username,
                    retreats
                )
                VALUES (?, ?, ?, 1)
                ON CONFLICT (guild_id, user_id)
                DO UPDATE SET
                    username = excluded.username,
                    retreats = retreats + 1,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (guild_id, user_id, username),
            )

        description = (
            f"🏃 **{username}** helped the dragon retreat safely."
        )

        _save_action(
            combat_id=int(combat["id"]),
            user_id=user_id,
            username=username,
            action_key=action_key,
            damage=0,
            description=description,
            turn=turn,
        )

        reset_to_idle(
            guild_id,
            reason="combat_retreat",
        )

        return CombatResult(
            combat_id=int(combat["id"]),
            enemy_key=enemy.key,
            enemy_name=enemy.name,
            enemy_emoji=enemy.emoji,
            description=description,
            dragon_hp=dragon_hp,
            dragon_max_hp=int(combat["dragon_max_hp"]),
            enemy_hp=enemy_hp,
            enemy_max_hp=int(combat["enemy_max_hp"]),
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

        loot, unlocked = _award_victory(
            combat_id=int(combat["id"]),
            guild_id=guild_id,
            user_id=user_id,
            username=username,
            enemy=enemy,
            dragon_hp=dragon_hp,
        )

        xp_reward = enemy.xp_reward
        token_reward = enemy.token_reward

        apply_combat_aftermath(guild_id)

        set_state(
            guild_id,
            DragonState.RECOVERING,
            duration=timedelta(seconds=60),
            payload={
                "reason": "combat_victory",
                "combat_id": int(combat["id"]),
            },
            force=True,
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
                "💔 The dragon was defeated and must recover."
            )

            with db_session() as connection:
                connection.execute(
                    """
                    INSERT INTO player_combat_progress_v5 (
                        guild_id,
                        user_id,
                        username,
                        defeats
                    )
                    VALUES (?, ?, ?, 1)
                    ON CONFLICT (guild_id, user_id)
                    DO UPDATE SET
                        username = excluded.username,
                        defeats = defeats + 1,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        guild_id,
                        user_id,
                        username,
                    ),
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

    description = "\n".join(log_lines)

    _save_action(
        combat_id=int(combat["id"]),
        user_id=user_id,
        username=username,
        action_key=action_key,
        damage=damage,
        description=description,
        turn=turn,
    )

    return CombatResult(
        combat_id=int(combat["id"]),
        enemy_key=enemy.key,
        enemy_name=enemy.name,
        enemy_emoji=enemy.emoji,
        description=description,
        dragon_hp=dragon_hp,
        dragon_max_hp=int(combat["dragon_max_hp"]),
        enemy_hp=enemy_hp,
        enemy_max_hp=int(combat["enemy_max_hp"]),
        status=status,
        turn_number=turn,
        xp_reward=xp_reward,
        token_reward=token_reward,
        loot=tuple(loot),
        unlocked_achievements=tuple(unlocked),
    )


def _save_action(
    *,
    combat_id: int,
    user_id: int,
    username: str,
    action_key: str,
    damage: int,
    description: str,
    turn: int,
) -> None:
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
                contribution =
                    contribution + excluded.contribution,
                last_action = excluded.last_action,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                combat_id,
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
                combat_id,
                user_id,
                action_key,
                damage,
                description,
                turn,
            ),
        )
