import discord

from database import get_dragon, connect
from utils import emoji_bar, growth_bar, heart_bar, get_stage, get_stage_title, detailed_stage_title, next_stage_info, time_of_day, current_season
from shop import SHOP, has_item
from achievements import ACHIEVEMENTS, get_user_achievements
from art_engine import attach_visual, art_status, needed_images_for_stage
from world import current_world, world_progress_bar, unlocked_world_text
from progression import RESEARCH, has_research, level_needed
from traits import trait_description
from visual_theme import (
    compact_care_line,
    xp_bar,
    hearts,
    mood_color,
    lair_emoji,
    event_emoji,
    stage_icon,
    dragon_status_badge,
    separator,
    rarity_from_tokens,
    dragon_element,
)


def make_dragon_embed(guild_id: int):
    d = get_dragon(guild_id)

    stage, emoji = get_stage(d["xp"])
    stage_title, _ = detailed_stage_title(d["xp"])
    progress, current_xp, next_xp, next_name = next_stage_info(d["xp"])
    world_now, world_next = current_world(d["lifetime_guild_tokens"])

    next_world = "Final milestone reached"
    if world_next:
        next_world = f"{world_next[1]} at {world_next[0]} lifetime tokens"

    status = dragon_status_badge(d)
    rarity = rarity_from_tokens(d["lifetime_guild_tokens"])
    element = dragon_element(d["dragon_color"])

    embed = discord.Embed(
        title=f"{stage_icon(stage_title)} {d['dragon_name']}",
        description=(
            f"## {stage_title} • {d['dragon_color']} Dragon\n"
            f"`{status}`  `{rarity}`  `{element}`\n"
            f"💭 *\"{d['dragon_message']}\"*\n"
            f"{separator()}\n"
            f"{lair_emoji(d['lair'])} **Lair:** `{d['lair']}`  •  🌍 **World:** `{world_now[1]}`\n"
            f"🧠 **Personality:** `{d['personality']}`  •  😊 **Mood:** `{d['mood']}`\n"
            f"🌟 **Trait:** `{d['dragon_trait']}`  •  🎩 **Accessory:** `{d['accessory']}`\n"
            f"☀️ **Sky:** `{time_of_day()} · {d['weather']}`  •  🌸 **Season:** `{current_season()}`\n"
            f"💤 **Sleeping:** `{'Yes' if d['sleeping'] else 'No'}`  •  {event_emoji(d['world_event'])} **Event:** `{d['world_event']}`"
        ),
        color=mood_color(d),
    )

    embed.add_field(
        name="⭐ Growth",
        value=(
            f"**Next:** `{next_name}`\n"
            f"{xp_bar(progress, 100)} `{progress}%`\n"
            f"**XP:** `{d['xp']} / {next_xp}`"
        ),
        inline=False,
    )

    embed.add_field(
        name="🐉 Care",
        value=(
            f"{compact_care_line('🍖', 'Hunger', d['hunger'])}\n"
            f"{compact_care_line('😊', 'Happy', d['happiness'])}\n"
            f"{compact_care_line('⚡', 'Energy', d['energy'])}\n"
            f"{compact_care_line('💧', 'Clean', d['cleanliness'])}"
        ),
        inline=False,
    )

    embed.add_field(name="💞 Bond", value=hearts(d["bond"]), inline=False)

    embed.add_field(
        name="🌍 World",
        value=(
            f"**Lifetime:** `{d['lifetime_guild_tokens']}` tokens\n"
            f"{world_progress_bar(d['lifetime_guild_tokens'])}\n"
            f"**Next:** {next_world}"
        ),
        inline=False,
    )

    embed.add_field(
        name="🐲 Guild",
        value=(
            f"Level **{d['guild_level']}** • Prestige **{d['prestige']}**\n"
            f"Research Points: **{d['research_points']}**\n"
            f"`{d['guild_level_xp']} / {level_needed(d['guild_level'])}` Guild XP"
        ),
        inline=True,
    )

    embed.add_field(name="🪙 Tokens", value=f"Spendable: **{d['guild_tokens']}**", inline=True)
    embed.add_field(name="📝 Last Action", value=d["last_action_text"], inline=False)
    embed.set_footer(text="Visual Assets v3.7 • Dragon artwork active")

    embed, file = attach_visual(embed, stage, d["pose"], d["lair"], d["weather"], d["visual_event"], world_now[1])
    return embed, file


def make_world_embed(guild_id: int):
    d = get_dragon(guild_id)
    world_now, world_next = current_world(d["lifetime_guild_tokens"])

    next_text = "The guild has reached the final known world milestone."
    if world_next:
        needed = world_next[0] - d["lifetime_guild_tokens"]
        next_text = f"Next: **{world_next[1]}** in **{needed}** lifetime tokens."

    embed = discord.Embed(
        title="🌍 Dragon World Progression",
        description=(
            f"Current World: **{world_now[1]}**\n"
            f"{world_now[2]}\n\n"
            f"Lifetime Guild Tokens: **{d['lifetime_guild_tokens']}**\n"
            f"{world_progress_bar(d['lifetime_guild_tokens'])}\n\n"
            f"{next_text}"
        ),
        color=0x7B2CFF,
    )
    embed.add_field(name="Unlocked World Features", value=unlocked_world_text(d["lifetime_guild_tokens"]), inline=False)
    return embed


def make_shop_embed(guild_id: int):
    d = get_dragon(guild_id)
    embed = discord.Embed(
        title="🛒 Guild Dragon Shop",
        description=(
            f"Spendable Guild Tokens: **{d['guild_tokens']}**\n"
            f"Lifetime Guild Tokens: **{d['lifetime_guild_tokens']}**\n\n"
            f"Buy upgrades with the dropdown below."
        ),
        color=0xE2B714,
    )
    for key, item in SHOP.items():
        status = "✅ Bought" if has_item(guild_id, key) else f"Cost: {item['cost']}"
        embed.add_field(name=f"{item['name']} — {status}", value=item["description"], inline=False)
    return embed


def make_research_embed(guild_id: int):
    d = get_dragon(guild_id)
    embed = discord.Embed(
        title="📚 Dragon Research",
        description=(
            f"Guild Level: **{d['guild_level']}**\n"
            f"Guild XP: **{d['guild_level_xp']} / {level_needed(d['guild_level'])}**\n"
            f"Research Points: **{d['research_points']}**\n"
            f"Prestige: **{d['prestige']}**\n\n"
            f"Research unlocks permanent bonuses for the whole guild."
        ),
        color=0x7B2CFF,
    )
    for key, item in RESEARCH.items():
        status = "✅ Unlocked" if has_research(guild_id, key) else f"Cost: {item['cost']} RP"
        embed.add_field(name=f"{item['name']} — {status}", value=item["description"], inline=False)
    return embed


def make_progression_embed(guild_id: int):
    d = get_dragon(guild_id)
    needed = level_needed(d["guild_level"])
    embed = discord.Embed(
        title="🐲 Guild Progression",
        description=(
            f"Guild Level: **{d['guild_level']}**\n"
            f"Guild XP: **{d['guild_level_xp']} / {needed}**\n"
            f"Research Points: **{d['research_points']}**\n"
            f"Prestige: **{d['prestige']}**\n\n"
            f"Guild XP is earned whenever members care for the dragon or claim events."
        ),
        color=0x7B2CFF,
    )
    unlocked = []
    locked = []
    for key, item in RESEARCH.items():
        if has_research(guild_id, key):
            unlocked.append(f"✅ {item['name']}")
        else:
            locked.append(f"🔒 {item['name']} ({item['cost']} RP)")
    embed.add_field(name="Unlocked Research", value="\n".join(unlocked) if unlocked else "No research yet.", inline=False)
    embed.add_field(name="Locked Research", value="\n".join(locked) if locked else "All research unlocked.", inline=False)
    return embed


def make_profile_embed(guild, member):
    con = connect()
    con.row_factory = __import__("sqlite3").Row
    cur = con.cursor()
    cur.execute("SELECT * FROM players WHERE guild_id=? AND user_id=?", (guild.id, member.id))
    p = cur.fetchone()
    con.close()

    if not p:
        return discord.Embed(title=f"🎖️ {member.display_name}'s Dragon Profile", description="No progress yet.", color=0x7B2CFF)

    achievements = get_user_achievements(guild.id, member.id)
    achievement_lines = [ACHIEVEMENTS[key][0] for key in achievements[:12] if key in ACHIEVEMENTS]
    title = p["keeper_title"] or "Dragon Keeper"
    embed = discord.Embed(
        title=f"🎖️ {member.display_name}'s Dragon Profile",
        description=(
            f"**Title:** {title}\n"
            f"**Points:** {p['points']}\n"
            f"**Tokens:** {p['tokens']}\n"
            f"🔥 **Current Streak:** {p['streak']} days\n"
            f"🏆 **Best Streak:** {p['best_streak']} days"
        ),
        color=0x7B2CFF,
    )
    embed.add_field(
        name="Care Stats",
        value=(
            f"🍖 Feeds: **{p['feeds']}**\n"
            f"🎾 Plays: **{p['plays']}**\n"
            f"🏋️ Trains: **{p['trains']}**\n"
            f"🛁 Cleans: **{p['cleans']}**\n"
            f"😴 Rests: **{p['rests']}**\n"
            f"❤️ Bonds: **{p['bonds']}**\n"
            f"🎁 Events: **{p['events']}**"
        ),
        inline=False,
    )
    embed.add_field(name="Achievements", value="\n".join(achievement_lines) if achievement_lines else "No achievements yet.", inline=False)
    return embed


def make_leaderboard_embed(guild):
    con = connect()
    cur = con.cursor()
    cur.execute("SELECT user_id, points, tokens FROM players WHERE guild_id=? ORDER BY points DESC LIMIT 10", (guild.id,))
    rows = cur.fetchall()
    con.close()

    desc = ""
    for i, row in enumerate(rows, start=1):
        member = guild.get_member(row[0])
        name = member.display_name if member else f"User {row[0]}"
        desc += f"**{i}. {name}** — {row[1]} points | {row[2]} tokens\n"
    return discord.Embed(title="🏆 Top Dragon Keepers", description=desc or "No keepers yet.", color=0xF1C40F)


def make_memories_embed(guild_id: int):
    from memories import get_memories
    memories = get_memories(guild_id, limit=10)
    desc = "No memories yet." if not memories else "\n".join([f"• {m[0]}" for m in memories])
    return discord.Embed(title="📖 Dragon Memories", description=desc, color=0x9B59FF)


def make_art_status_embed(guild_id: int):
    d = get_dragon(guild_id)
    stage, _ = get_stage(d["xp"])
    world_now, _ = current_world(d["lifetime_guild_tokens"])
    status = art_status(stage, d["pose"], d["lair"], d["weather"], d["accessory"], d["visual_event"], world_now[1])
    embed = discord.Embed(
        title="🎨 Dragon Art Engine Status",
        description=(
            f"**Stage:** {stage}\n"
            f"**Pose:** {d['pose']}\n"
            f"**Lair:** {d['lair']}\n"
            f"**Weather:** {status['weather']}\n"
            f"**Time:** {status['time_of_day']}\n"
            f"**Accessory:** {d['accessory']}\n"
            f"**Event visual:** {d['visual_event']}\n"
            f"**World visual:** {world_now[1]}"
        ),
        color=0x7B2CFF,
    )
    embed.add_field(name="Dragon image", value=f"`{status['dragon_image']}`", inline=False)
    embed.add_field(name="Lair image", value=f"`{status['lair_image']}`", inline=False)
    embed.add_field(name="World image", value=f"`{status['world_image']}`", inline=False)
    embed.add_field(name="Event image", value=f"`{status['event_image']}`", inline=False)
    embed.add_field(name="Accessory image", value=f"`{status['accessory_image']}`", inline=False)
    return embed


def make_needed_images_embed(guild_id: int):
    d = get_dragon(guild_id)
    stage, _ = get_stage(d["xp"])
    needed = needed_images_for_stage(stage)
    embed = discord.Embed(title="🖼️ Needed Dragon Images", description=f"Current stage: **{stage}**\nUpload images with these names:", color=0x7B2CFF)
    embed.add_field(name="Files", value="\n".join(f"`{x}`" for x in needed), inline=False)
    embed.add_field(
        name="Optional images",
        value=(
            "`assets/world/empty_cave.png`\n"
            "`assets/world/soft_nest.png`\n"
            "`assets/events/treasure.png`\n"
            "`assets/events/merchant.png`\n"
            "`assets/events/storm.png`"
        ),
        inline=False,
    )
    return embed


def make_trait_embed(guild_id: int):
    trait, desc = trait_description(guild_id)
    return discord.Embed(
        title="🌟 Dragon Trait",
        description=f"Trait: **{trait}**\n{desc}\n\nThe dragon's trait affects some living dialogue and behavior.",
        color=0x7B2CFF,
    )
