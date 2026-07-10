from __future__ import annotations

import discord

from systems.state.models import DragonState
from systems.state.service import resolve_expired_state


def build_view(guild_id: int) -> discord.ui.View:
    state_record = resolve_expired_state(guild_id)

    if state_record.state == DragonState.SLEEPING:
        from ui.views.sleeping_view import SleepingView

        return SleepingView(guild_id)

    if state_record.state == DragonState.ADVENTURE:
        from ui.views.adventure_view import AdventureStateView

        return AdventureStateView(guild_id)

    if state_record.state == DragonState.COMBAT:
        from ui.views.combat_view import CombatStateView

        return CombatStateView(guild_id)

    if state_record.state == DragonState.RECOVERING:
        from ui.views.recovering_view import RecoveringView

        return RecoveringView(guild_id)

    if state_record.state == DragonState.CELEBRATING:
        from ui.views.celebrating_view import CelebratingView

        return CelebratingView(guild_id)

    from ui.views.idle_view import IdleView

    return IdleView(guild_id)
