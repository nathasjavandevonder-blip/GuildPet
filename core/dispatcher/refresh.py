from __future__ import annotations

import logging

log = logging.getLogger(__name__)


class RefreshManager:

    async def refresh_panel(
        self,
        guild_id: int,
    ) -> None:

        log.info(
            "Panel refresh requested for guild %s",
            guild_id,
        )

        #
        # Will hook into GuildPetPanel later.
        #


refresh_manager = RefreshManager()
