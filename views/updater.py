from database import get_dragon
from embeds import make_dragon_embed

async def update_dragon_message(guild):
    from views.dragon_view import DragonView

    d = get_dragon(guild.id)
    if not d["channel_id"] or not d["message_id"]:
        return

    channel = guild.get_channel(d["channel_id"])
    if not channel:
        return

    try:
        msg = await channel.fetch_message(d["message_id"])
        await msg.edit(embed=make_dragon_embed(guild.id), view=DragonView())
    except Exception:
        pass
