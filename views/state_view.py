from database import get_dragon

def get_state_view(guild_id: int):
    d = get_dragon(guild_id)

    if d["sleeping"]:
        from views.sleeping_view import SleepingView
        return SleepingView()

    from views.dragon_view import DragonView
    return DragonView()
