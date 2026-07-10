from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from core.database import db_session
from systems.state.models import DragonState, StateRecord


ALLOWED_TRANSITIONS: dict[DragonState, set[DragonState]] = {
    DragonState.IDLE: {
        DragonState.SLEEPING,
        DragonState.ADVENTURE,
        DragonState.COMBAT,
        DragonState.CELEBRATING,
    },
    DragonState.SLEEPING: {
        DragonState.IDLE,
    },
    DragonState.ADVENTURE: {
        DragonState.IDLE,
        DragonState.COMBAT,
        DragonState.RECOVERING,
        DragonState.CELEBRATING,
    },
    DragonState.COMBAT: {
        DragonState.ADVENTURE,
        DragonState.IDLE,
        DragonState.RECOVERING,
        DragonState.CELEBRATING,
    },
    DragonState.RECOVERING: {
        DragonState.IDLE,
        DragonState.SLEEPING,
    },
    DragonState.CELEBRATING: {
        DragonState.IDLE,
        DragonState.SLEEPING,
    },
}


class InvalidStateTransition(ValueError):
    pass


def utc_now() -> datetime:
    return datetime.now(UTC)


def _serialize_datetime(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    parsed = datetime.fromisoformat(value)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)

    return parsed


def ensure_state(guild_id: int) -> StateRecord:
    with db_session() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO dragon_state_v5 (
                guild_id,
                state,
                state_started_at,
                state_payload,
                updated_at
            )
            VALUES (?, 'idle', CURRENT_TIMESTAMP, '{}', CURRENT_TIMESTAMP)
            """,
            (guild_id,),
        )

    return get_state(guild_id)


def get_state(guild_id: int) -> StateRecord:
    with db_session() as connection:
        row = connection.execute(
            """
            SELECT
                guild_id,
                state,
                state_started_at,
                state_ends_at,
                state_payload
            FROM dragon_state_v5
            WHERE guild_id = ?
            """,
            (guild_id,),
        ).fetchone()

    if row is None:
        return ensure_state(guild_id)

    try:
        payload = json.loads(row["state_payload"] or "{}")
    except json.JSONDecodeError:
        payload = {}

    return StateRecord(
        guild_id=row["guild_id"],
        state=DragonState(row["state"]),
        started_at=_parse_datetime(row["state_started_at"]) or utc_now(),
        ends_at=_parse_datetime(row["state_ends_at"]),
        payload=payload,
    )


def can_transition(
    current_state: DragonState,
    target_state: DragonState,
) -> bool:
    if current_state == target_state:
        return True

    return target_state in ALLOWED_TRANSITIONS[current_state]


def set_state(
    guild_id: int,
    target_state: DragonState,
    *,
    duration: timedelta | None = None,
    payload: dict[str, Any] | None = None,
    force: bool = False,
) -> StateRecord:
    current = ensure_state(guild_id)

    if not force and not can_transition(current.state, target_state):
        raise InvalidStateTransition(
            f"Cannot transition from {current.state.value} "
            f"to {target_state.value}."
        )

    now = utc_now()
    ends_at = now + duration if duration else None
    state_payload = json.dumps(payload or {}, separators=(",", ":"))

    with db_session() as connection:
        connection.execute(
            """
            UPDATE dragon_state_v5
            SET
                state = ?,
                state_started_at = ?,
                state_ends_at = ?,
                state_payload = ?,
                updated_at = ?
            WHERE guild_id = ?
            """,
            (
                target_state.value,
                _serialize_datetime(now),
                _serialize_datetime(ends_at),
                state_payload,
                _serialize_datetime(now),
                guild_id,
            ),
        )

    return get_state(guild_id)


def reset_to_idle(
    guild_id: int,
    *,
    reason: str | None = None,
) -> StateRecord:
    payload = {"reason": reason} if reason else {}

    return set_state(
        guild_id,
        DragonState.IDLE,
        payload=payload,
        force=True,
    )


def resolve_expired_state(guild_id: int) -> StateRecord:
    current = ensure_state(guild_id)

    if not current.has_expired(utc_now()):
        return current

    return reset_to_idle(
        guild_id,
        reason=f"{current.state.value}_timer_finished",
    )


def start_sleep(
    guild_id: int,
    *,
    duration_minutes: int | None = None,
) -> StateRecord:
    duration = (
        timedelta(minutes=duration_minutes)
        if duration_minutes is not None
        else None
    )

    return set_state(
        guild_id,
        DragonState.SLEEPING,
        duration=duration,
        payload={"sleep_phase": "light_sleep"},
    )


def wake_dragon(
    guild_id: int,
    *,
    keeper_id: int | None = None,
    gentle: bool = True,
) -> StateRecord:
    payload: dict[str, Any] = {
        "wake_method": "gentle" if gentle else "normal",
    }

    if keeper_id is not None:
        payload["keeper_id"] = keeper_id

    return set_state(
        guild_id,
        DragonState.IDLE,
        payload=payload,
    )
