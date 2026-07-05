import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN")
DB_FILE = os.getenv("DB_FILE", "guild_dragon.db")
ASSET_BASE_PATH = os.getenv("ASSET_BASE_PATH", "assets")

# Only this Discord user ID may use slash commands.
# Put this in .env, for example: BOT_OWNER_ID=123456789012345678
BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID", "0") or "0")
