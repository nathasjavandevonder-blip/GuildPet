import discord
from database import get_dragon, connect
from utils import emoji_bar, growth_bar, heart_bar, get_stage, get_stage_title, next_stage_info
from shop import SHOP, has_item
from achievements import ACHIEVEMENTS, get_user_achievements
from visuals import attach_visual

def make_dragon_embed(guild_id: int):
    d = get_dragon(guild_id)
    stage, emoji = get_stage(d["xp"])
    stage_title, _ = get_stage_title(d["xp"])
    progress, current_xp, next_xp, next_name = next_stage_info(d["xp"])

    embed = discord.Embed(
        title=f"{emoji} {d['dragon_name']}",
        description=(
            f"**{stage_title}** · {d['dragon_color']} Dragon\n"
            f"🏡 **Lair:** {d['lair']}\n"
            f"🧠 **Personality:** {d['personality']}\n"
            f"😊 **Mood:** {d['mood']}\n\n"
            f"⭐ **Progress to {next_name}:** {d['xp']} / {next_xp}\n"
            f"{growth_bar(progress)}"
        ),
        color=0x7B2CFF
    )

    embed.add_field(name="🍖 Hunger", value=emoji_bar(d["hunger"]), inline=False)
    embed.add_field(name="😊 Happiness", value=emoji_bar(d["happiness"]), inline=False)
    embed.add_field(name="⚡ Energy", value=emoji_bar(d["energy"]), inline=False)
    embed.add_field(name="💧 Cleanliness", value=emoji_bar(d["cleanliness"]), inline=False)
    embed.add_field(name="💞 Guild Bond", value=heart_bar(d["bond"]), inline=False)

    embed.add_field(name="🪙 Guild Tokens", value=f"**{d['guild_tokens']}**", inline=True)
    embed.add_field(name="💭 The Dragon", value=f"*\"{d['dragon_message']}\"*", inline=False)
    embed.add_field(name="Last action", value=d["last_action_text"], inline=False)
    embed.set_footer(text="Buttons edit this one message to avoid spam.")

    embed, file = attach_visual(embed, stage, d["pose"])
    return embed, file

def make_shop_embed(guild_id: int):
    d = get_dragon(guild_id)
    embed = discord.Embed(
        title="🛒 Guild Dragon Shop",
        description=f"Guild Tokens: **{d['guild_tokens']}**\nBuy upgrades with the dropdown below.",
        color=0xE2B714
    )

    for key, item in SHOP.items():
        status = "✅ Bought" if has_item(guild_id, key) else f"Cost: {item['cost']}"
        embed.add_field(name=f"{item['name']} — {status}", value=item["description"], inline=False)

    return embed

def make_profile_embed(guild, member):
    con = connect()
    con.row_factory = __import__("sqlite3").Row
    cur = con.cursor()
    cur.execute("SELECT * FROM players WHERE guild_id=? AND user_id=?", (guild.id, member.id))
    p = cur.fetchone()
    con.close()

    if not p:
        embed = discord.Embed(title=f"🐉 {member.display_name}'s Dragon Profile", description="No progress yet.", color=0x7B2CFF)
        return embed

    achievements = get_user_achievements(guild.id, member.id)
    achievement_lines = []
    for key in achievements[:12]:
        if key in ACHIEVEMENTS:
            achievement_lines.append(ACHIEVEMENTS[key][0])

    title = p["keeper_title"] or "Dragon Keeper"

    embed = discord.Embed(
        title=f"🐉 {member.display_name}'s Dragon Profile",
        description=(
            f"**Title:** {title}\n"
            f"**Points:** {p['points']}\n"
            f"**Tokens:** {p['tokens']}\n"
            f"🔥 **Current Streak:** {p['streak']} days\n"
            f"🌟 **Best Streak:** {p['best_streak']} days"
        ),
        color=0x7B2CFF
    )
    embed.add_field(name="Care Stats", value=(
        f"🍖 Feeds: **{p['feeds']}**\n"
        f"🎾 Plays: **{p['plays']}**\n"
        f"🏋️ Trains: **{p['trains']}**\n"
        f"🛁 Cleans: **{p['cleans']}**\n"
        f"😴 Rests: **{p['rests']}**\n"
        f"❤️ Bonds: **{p['bonds']}**\n"
        f"🎁 Events: **{p['events']}**"
    ), inline=False)
    embed.add_field(name="Achievements", value="\n".join(achievement_lines) if achievement_lines else "No achievements yet.", inline=False)
    return embed
