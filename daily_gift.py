from datetime import datetime, timezone
import random
import discord
from database import connect, get_dragon
from memories import add_memory

def today_key():
    return datetime.now(timezone.utc).date().isoformat()

def daily_gift_available(guild_id: int):
    d = get_dragon(guild_id)
    return d["last_daily_gift"] != today_key()

def claim_daily_gift(guild_id: int, user):
    if not daily_gift_available(guild_id):
        return False, "🎁 The daily guild gift has already been claimed today."

    reward = random.randint(50, 125)

    con = connect()
    cur = con.cursor()
    cur.execute("""
        UPDATE dragon
        SET guild_tokens=guild_tokens+?,
            lifetime_guild_tokens=lifetime_guild_tokens+?,
            last_daily_gift=?,
            visual_event=?,
            dragon_message=?,
            last_action_text=?
        WHERE guild_id=?
    """, (
        reward,
        reward,
        today_key(),
        "daily_gift",
        "I found something shiny for the guild!",
        f"🎁 **{user.display_name}** claimed the daily guild gift: **{reward} Guild Tokens**.",
        guild_id,
    ))
    con.commit()
    con.close()

    add_memory(guild_id, f"{user.display_name} claimed the daily guild gift worth {reward} Guild Tokens.")
    return True, f"🎁 **{user.display_name}** claimed the daily guild gift and added **{reward} Guild Tokens**!"

class DailyGiftView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim Gift", emoji="🎁", style=discord.ButtonStyle.success, custom_id="dragon_daily_gift_claim")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        from views.updater import update_dragon_message

        ok, msg = claim_daily_gift(interaction.guild.id, interaction.user)

        if ok:
            await interaction.response.edit_message(content=msg, embed=None, view=None)
            await update_dragon_message(interaction.guild)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
