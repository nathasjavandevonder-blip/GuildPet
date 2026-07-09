from database import get_dragon
from embeds import make_dragon_embed

async def update_dragon_message(guild):
    from views.state_view import get_state_view
    d = get_dragon(guild.id)
    if not d["channel_id"] or not d["message_id"]: return
    channel = guild.get_channel(d["channel_id"])
    if not channel: return
    try:
        msg = await channel.fetch_message(d["message_id"])
        embed, file = make_dragon_embed(guild.id)
        if file:
            await msg.edit(embed=embed, attachments=[file], view=get_state_view(interaction.guild.id))
        else:
            await msg.edit(embed=embed, attachments=[], view=get_state_view(interaction.guild.id))
    except Exception as e:
        print(f"Failed to update dragon message: {e}")
