import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN")
DB_FILE = os.getenv("DB_FILE", "guild_dragon.db")

# Set this to a Discord channel ID where the bot may upload generated/attached images later.
# For now this is optional.
ASSET_UPLOAD_CHANNEL_ID = int(os.getenv("ASSET_UPLOAD_CHANNEL_ID", "0"))

# Local fallback images. Put PNG/JPG/WebP files inside assets/dragons/<stage>/<pose>.png
ASSET_BASE_PATH = "assets"
