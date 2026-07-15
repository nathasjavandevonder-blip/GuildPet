from __future__ import annotations

import discord

from core.dashboard_renderer import DashboardRenderer
from core.dragon_service import service
from core.guild_settings import get_guild_language


def build_main_embed(guild_id: int) -> discord.Embed:
    """Build the single permanent GuildPet dashboard."""
    status = service.status(guild_id)
    language = get_guild_language(guild_id)
    return DashboardRenderer(status, language).build()
