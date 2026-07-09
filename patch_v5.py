from pathlib import Path

# add v5 extension
p = Path("bot.py")
text = p.read_text()
if '"cogs.v5"' not in text:
    text = text.replace('"cogs.adventures",', '"cogs.adventures", "cogs.v5",')
p.write_text(text)

# patch dragon.py so normal care buttons also count for v5
p = Path("dragon.py")
text = p.read_text()

if "from v5_systems import record_contribution" not in text:
    text = text.replace(
        "from rpg import progress_quest, set_quest_progress",
        "from rpg import progress_quest, set_quest_progress\nfrom v5_systems import record_contribution, add_memory as add_v5_memory"
    )

needle = 'streak, new_day = add_player_reward(guild_id, user.id, e["tokens"], e["points"], action)'
insert = '''streak, new_day = add_player_reward(guild_id, user.id, e["tokens"], e["points"], action)
    try:
        record_contribution(guild_id, user, action, 2)
        if action in ["feed", "play", "train", "clean", "bond"] and random.random() < 0.08:
            add_v5_memory(guild_id, f"{user.display_name} {e['text'].strip()} and helped shape my personality.", user=user, memory_type="Care", importance=1)
    except Exception as exc:
        print(f"v5 contribution tracking failed: {exc}")'''

if "v5 contribution tracking failed" not in text:
    if needle in text:
        text = text.replace(needle, insert)
    else:
        print("WARNING: Could not auto-patch dragon.py contribution hook.")

p.write_text(text)
