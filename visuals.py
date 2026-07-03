from pathlib import Path
import discord
from config import ASSET_BASE_PATH

STAGE_FOLDER = {
    "Egg": "egg",
    "Hatchling": "hatchling",
    "Young Dragon": "young_dragon",
    "Adult Dragon": "adult_dragon",
    "Ancient Dragon": "ancient_dragon",
    "Elder Dragon": "elder_dragon",
}

POSE_FALLBACKS = {
    "eating": ["eating", "happy", "idle"],
    "playing": ["playing", "happy", "idle"],
    "training": ["training", "fire", "idle"],
    "clean": ["clean", "happy", "idle"],
    "sleeping": ["sleeping", "idle"],
    "bonding": ["bonding", "happy", "idle"],
    "looking around": ["idle"],
    "stretching": ["idle"],
    "guarding the lair": ["idle"],
    "waiting": ["idle"],
}

VALID_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp"]


def get_asset_path(stage: str, pose: str):
    stage_folder = STAGE_FOLDER.get(stage, "egg")
    pose_options = POSE_FALLBACKS.get(pose, [pose, "idle"])

    for pose_name in pose_options:
        for ext in VALID_EXTENSIONS:
            path = Path(ASSET_BASE_PATH) / "dragons" / stage_folder / f"{pose_name}{ext}"
            if path.exists():
                return path

    return None


def attach_visual(embed: discord.Embed, stage: str, pose: str):
    path = get_asset_path(stage, pose)
    if not path:
        return embed, None

    file = discord.File(str(path), filename=path.name)
    embed.set_image(url=f"attachment://{path.name}")
    return embed, file
