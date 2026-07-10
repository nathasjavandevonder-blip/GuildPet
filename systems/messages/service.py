from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import discord

from core.config import settings
from core.database import db_session


async def delete_later(
    message: discord.Message,
    *,
    seconds: int,
) -> None:
    if seconds <= 0:
        return

    try:
        await asyncio.sleep(seconds)
        await message.delete()
    except discord.NotFound:
        pass
    except discord.Forbidden:
        pass
    except discord.HTTPException:
        pass


async def send_temporary(
    channel,
    content: str | None = None,
    *,
    embed: discord.Embed | None = None,
    view: discord.ui.View | None = None,
    seconds: int | None = None,
):
    lifetime = (
        settings.channel_message_minutes * 60
        if seconds is None
        else seconds
    )

    message = await channel.send(
        content=content,
        embed=embed,
        view=view,
        delete_after=lifetime,
    )

    return message


def register_temporary_message(
    *,
    guild_id: int,
    channel_id: int,
    message_id: int,
    message_type: str,
    seconds: int,
) -> None:
    delete_at = datetime.now(UTC) + timedelta(seconds=seconds)

    with db_session() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO temporary_messages (
                message_id,
                channel_id,
                guild_id,
                delete_at,
                message_type
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                message_id,
                channel_id,
                guild_id,
                delete_at.isoformat(),
                message_type,
            ),
        )


def remove_temporary_message(message_id: int) -> None:
    with db_session() as connection:
        connection.execute(
            "DELETE FROM temporary_messages WHERE message_id = ?",
            (message_id,),
        )
