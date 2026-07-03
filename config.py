import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN")
DB_FILE = os.getenv("DB_FILE", "guild_dragon.db")
ASSET_BASE_PATH = "assets"
