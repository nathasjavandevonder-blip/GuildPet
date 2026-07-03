import discord
from config import STAGE_IMAGES, LAIR_IMAGES
from database import get_dragon
from shop import SHOP, has_item
from utils import emoji_bar, growth_bar, get_stage, next_stage_info

def make_dragon_embed(guild_id: int):
    d = get_dragon(guild_id)
    stage, emoji = get_stage(d["xp"])
    progress, current_xp, next_xp, next_name = next_stage_info(d["xp"])

    embed = discord.Embed(
        title=f"{emoji} Guild Dragon",
        description=(
            f"**Stage:** {stage}\n"
            f"**Lair:** {d['lair']}\n"
            f"**Personality:** {d['personality']}\n"
            f"**Guild XP:** {d['xp']} / {next_xp}\n"
            f"**Next stage:** {next_name}\n"
            f"**Growth:** {growth_bar(progress)}"
        ),
        color=0x7B2CFF
    )

    embed.add_field(name="🍖 Hunger", value=emoji_bar(d["hunger"]), inline=False)
    embed.add_field(name="😊 Happiness", value=emoji_bar(d["happiness"]), inline=False)
    embed.add_field(name="⚡ Energy", value=emoji_bar(d["energy"]), inline=False)
    embed.add_field(name="💧 Cleanliness", value=emoji_bar(d["cleanliness"]), inline=False)
    embed.add_field(name="❤️ Bond", value=emoji_bar(d["bond"]), inline=False)

    embed.add_field(name="🪙 Guild Tokens", value=f"{d['guild_tokens']}", inline=True)
    embed.add_field(name="🎭 Pose", value=d["pose"], inline=True)
    embed.add_field(name="🐉 Dragon says", value=d["dragon_message"], inline=False)
    embed.add_field(name="Last action", value=d["last_action_text"], inline=False)

    image_url = LAIR_IMAGES.get(d["lair"]) or STAGE_IMAGES.get(stage)
    if image_url:
        embed.set_image(url=image_url)

    embed.set_footer(text="Buttons edit this one message to avoid spam.")
    return embed

def make_shop_embed(guild_id: int):
    d = get_dragon(guild_id)
    embed = discord.Embed(
        title="🛒 Guild Dragon Shop",
        description=f"Guild Tokens: **{d['guild_tokens']}**\nBuy upgrades with the dropdown below.",
        color=0xE2B714
    )

    for key, item in SHOP.items():
        status = "✅ Bought" if has_item(guild_id, key) else f"Cost: {item['cost']}"
        embed.add_field(
            name=f"{item['name']} — {status}",
            value=item["description"],
            inline=False
        )
    return embed
