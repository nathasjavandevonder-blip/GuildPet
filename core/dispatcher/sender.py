from __future__ import annotations

import logging
from typing import Any

import discord

log = logging.getLogger(__name__)


class DiscordSender:

    async def send(
        self,
        *,
        channel: discord.abc.Messageable,
        content: str | None = None,
        embed: discord.Embed | None = None,
        view: discord.ui.View | None = None,
        file: discord.File | None = None,
    ) -> discord.Message:

        kwargs: dict[str, Any] = {}

        if content is not None:
            kwargs["content"] = content

        if embed is not None:
            kwargs["embed"] = embed

        if view is not None:
            kwargs["view"] = view

        if file is not None:
            kwargs["file"] = file

        message = await channel.send(**kwargs)

        log.info(
            "Sent dispatcher message %s",
            message.id,
        )

        return message


discord_sender = DiscordSender()
