from pathlib import Path
import discord

from config import ASSET_BASE_PATH
from utils import time_of_day

STAGE_FOLDER = {
    "Egg": "egg",
    "Hatchling": "hatchling",
    "Young Dragon": "young_dragon",
    "Adult Dragon": "adult_dragon",
    "Ancient Dragon": "ancient_dragon",
    "Elder Dragon": "elder_dragon",
}

LAIR_FOLDER = {
    "Empty Cave": "empty_cave",
    "Moss Nest": "moss_nest",
    "Crystal Nest": "crystal_nest",
    "Lava Nest": "lava_nest",
    "Royal Dragon Hall": "royal_dragon_hall",
    "Sky Fortress": "sky_fortress",
}

POSE_FALLBACKS = {
    "eating": ["eating", "happy", "idle"],
    "playing": ["playing", "happy", "idle"],
    "training": ["training", "fire", "idle"],
    "clean": ["clean", "happy", "idle"],
    "sleeping": ["sleeping", "idle"],
    "bonding": ["bonding", "happy", "idle"],
    "celebrating": ["celebrating", "happy", "idle"],
    "sad": ["sad", "idle"],
    "adventuring": ["adventuring", "idle"],
    "looking around": ["idle"],
    "stretching": ["idle"],
    "guarding the lair": ["idle"],
    "waiting": ["idle"],
}

VALID_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp"]


def find_first(paths):
    for path in paths:
        for ext in VALID_EXTENSIONS:
            candidate = path.with_suffix(ext)
            if candidate.exists():
                return candidate
    return None


def safe_key(text: str):
    text = (text or "empty_cave").lower()
    keep = []
    for ch in text:
        if ch.isalnum():
            keep.append(ch)
        elif ch in [" ", "-", "_"]:
            keep.append("_")
    out = "".join(keep)
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_") or "empty_cave"


def dragon_asset(stage: str, pose: str):
    stage_folder = STAGE_FOLDER.get(stage, "egg")
    pose_options = POSE_FALLBACKS.get(pose, [safe_key(pose), "idle"])

    paths = []
    for pose_name in pose_options:
        pose_name = safe_key(pose_name)
        # New asset naming: hatchling_idle.png / young_dragon_training.png
        paths.append(Path(ASSET_BASE_PATH) / "dragons" / stage_folder / f"{stage_folder}_{pose_name}")
        # Old asset naming: idle.png / training.png
        paths.append(Path(ASSET_BASE_PATH) / "dragons" / stage_folder / pose_name)

    return find_first(paths)


def lair_asset(lair: str, weather: str):
    lair_folder = LAIR_FOLDER.get(lair, safe_key(lair))
    tod = time_of_day().lower()
    weather = safe_key(weather or "clear")
    paths = [
        Path(ASSET_BASE_PATH) / "lairs" / lair_folder / f"{tod}_{weather}",
        Path(ASSET_BASE_PATH) / "lairs" / lair_folder / tod,
        Path(ASSET_BASE_PATH) / "lairs" / lair_folder / weather,
        Path(ASSET_BASE_PATH) / "lairs" / lair_folder / "idle",
    ]
    return find_first(paths)


def accessory_asset(accessory: str):
    accessory = safe_key(accessory or "none")
    return find_first([Path(ASSET_BASE_PATH) / "accessories" / accessory / "idle"])


def event_asset(event_key: str):
    event_key = safe_key(event_key or "none")
    if event_key == "none":
        return None
    return find_first([
        Path(ASSET_BASE_PATH) / "events" / event_key,
        Path(ASSET_BASE_PATH) / "events" / "idle",
    ])


def world_asset(world_name: str):
    safe = safe_key(world_name)
    return find_first([
        Path(ASSET_BASE_PATH) / "world" / safe,
        Path(ASSET_BASE_PATH) / "world" / "idle",
    ])


def best_visual(stage: str, pose: str, lair: str, weather: str, visual_event: str = "None", world_name: str = ""):
    return event_asset(visual_event) or dragon_asset(stage, pose) or world_asset(world_name) or lair_asset(lair, weather)


def attach_visual(embed: discord.Embed, stage: str, pose: str, lair: str, weather: str, visual_event: str = "None", world_name: str = ""):
    path = best_visual(stage, pose, lair, weather, visual_event, world_name)
    if not path:
        return embed, None
    file = discord.File(str(path), filename=path.name)
    embed.set_image(url=f"attachment://{path.name}")
    return embed, file


def art_status(stage: str, pose: str, lair: str, weather: str, accessory: str, visual_event: str = "None", world_name: str = ""):
    return {
        "dragon_image": str(dragon_asset(stage, pose) or "missing"),
        "lair_image": str(lair_asset(lair, weather) or "missing"),
        "accessory_image": str(accessory_asset(accessory) or "missing"),
        "event_image": str(event_asset(visual_event) or "missing"),
        "world_image": str(world_asset(world_name) or "missing"),
        "time_of_day": time_of_day(),
        "weather": weather,
    }


def needed_images_for_stage(stage: str):
    folder = STAGE_FOLDER.get(stage, "egg")
    poses = ["idle", "eating", "playing", "training", "clean", "sleeping", "bonding", "celebrating", "sad", "adventuring"]
    return [f"assets/dragons/{folder}/{folder}_{pose}.png" for pose in poses]
