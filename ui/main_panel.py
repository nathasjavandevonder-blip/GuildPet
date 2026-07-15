from __future__ import annotations

import discord

from core.dashboard_renderer import DashboardRenderer
from core.dragon_service import service


def build_main_embed(guild_id: int) -> discord.Embed:
    """Build the single permanent GuildPet dashboard.

    All stage-specific gameplay remains in the view layer, while the dashboard
    itself now reads from one central DragonStatus model.
    """
    status = service.status(guild_id)
    return DashboardRenderer(status).build()
