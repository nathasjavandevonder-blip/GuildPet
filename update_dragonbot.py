from pathlib import Path
import re

# config.py: owner id support
p = Path("config.py")
s = p.read_text()
if "BOT_OWNER_ID" not in s:
    s += '\nBOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID", "0") or "0")\n'
p.write_text(s)

# bot.py: slash commands only for owner
p = Path("bot.py")
s = p.read_text()
s = s.replace("from config import TOKEN", "from config import TOKEN, BOT_OWNER_ID")

insert = '''
async def owner_only_interaction_check(interaction: discord.Interaction) -> bool:
    if BOT_OWNER_ID and interaction.user.id == BOT_OWNER_ID:
        return True
    await interaction.response.send_message("⛔ Only Nathasja can use slash commands.", ephemeral=True)
    return False

'''
if "owner_only_interaction_check" not in s:
    s = s.replace("bot = GuildDragonBot()\n", "bot = GuildDragonBot()\n\n" + insert + "bot.tree.interaction_check = owner_only_interaction_check\n")
p.write_text(s)

# utils.py: stage XP x55
p = Path("utils.py")
s = p.read_text()
s = re.sub(r'if xp >= 100000: return "Elder Dragon"', 'if xp >= 5500000: return "Elder Dragon"', s)
s = re.sub(r'if xp >= 40000: return "Ancient Dragon"', 'if xp >= 2200000: return "Ancient Dragon"', s)
s = re.sub(r'if xp >= 15000: return "Adult Dragon"', 'if xp >= 825000: return "Adult Dragon"', s)
s = re.sub(r'if xp >= 5000: return "Young Dragon"', 'if xp >= 275000: return "Young Dragon"', s)
s = re.sub(r'if xp >= 1000: return "Hatchling"', 'if xp >= 55000: return "Hatchling"', s)
s = re.sub(
    r'stages = \[\("Egg", 0\), \("Hatchling", 1000\), \("Young Dragon", 5000\), \("Adult Dragon", 15000\), \("Ancient Dragon", 40000\), \("Elder Dragon", 100000\)\]',
    'stages = [("Egg", 0), ("Hatchling", 55000), ("Young Dragon", 275000), ("Adult Dragon", 825000), ("Ancient Dragon", 2200000), ("Elder Dragon", 5500000)]',
    s
)
s = re.sub(r'if xp < 250:', 'if xp < 13750:', s)
s = re.sub(r'if xp < 500:', 'if xp < 27500:', s)
s = re.sub(r'if xp < 750:', 'if xp < 41250:', s)
s = re.sub(r'if xp < 1000:', 'if xp < 55000:', s)
p.write_text(s)

# dragon.py: rebalance energy/care
p = Path("dragon.py")
s = p.read_text()
s = s.replace('"feed": {"hunger": 10 + feed_bonus, "xp": 2', '"feed": {"hunger": 12 + feed_bonus, "energy": 3, "xp": 2')
s = s.replace('"play": {"happiness": 8, "energy": -5', '"play": {"happiness": 10, "energy": -2')
s = s.replace('"train": {"bond": 5, "energy": -10', '"train": {"bond": 5, "energy": -5')
s = s.replace('"clean": {"cleanliness": 10 + clean_bonus, "xp": 2', '"clean": {"cleanliness": 12 + clean_bonus, "energy": 2, "xp": 2')
s = s.replace('"rest": {"energy": 15', '"rest": {"energy": 35')
s = s.replace('"bond": {"bond": 8, "happiness": 3', '"bond": {"bond": 8, "happiness": 4, "energy": 2')
s = s.replace('clamp(d["hunger"] - 3)', 'clamp(d["hunger"] - 2)')
s = s.replace('clamp(d["happiness"] - 2)', 'clamp(d["happiness"] - 1)')
s = s.replace('clamp(d["energy"] - 2)', 'clamp(d["energy"] - 1)')
s = s.replace('clamp(d["cleanliness"] - 2)', 'clamp(d["cleanliness"] - 1)')
p.write_text(s)

# dragon_view.py: remove World button/import, keep Adventure
p = Path("dragon_view.py")
s = p.read_text()
s = s.replace(", make_world_embed", "")
s = re.sub(
    r'\n\s*@discord\.ui\.button\(label="World".*?\n\s*async def world\(self, interaction, button\):.*?\n\s*\)',
    '',
    s,
    flags=re.S
)
p.write_text(s)

print("Updated: config.py, bot.py, utils.py, dragon.py, dragon_view.py")
