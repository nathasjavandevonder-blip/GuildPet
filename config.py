import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN")
DB_FILE = os.getenv("DB_FILE", "guild_dragon.db")

# Put real Discord image URLs here later.
STAGE_IMAGES = {
    "Egg": "",
    "Hatchling": "",
    "Young Dragon": "",
    "Adult Dragon": "",
    "Ancient Dragon": "",
    "Elder Dragon": "",
}

LAIR_IMAGES = {
    "Empty Cave": "",
    "Moss Nest": "",
    "Crystal Nest": "",
    "Lava Nest": "",
    "Royal Dragon Hall": "",
    "Sky Fortress": "",
}
