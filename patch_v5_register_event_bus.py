from pathlib import Path

path = Path("bot_v5.py")
text = path.read_text(encoding="utf-8")

import_marker = (
    "from migrations.manager import run_migrations\n"
)

new_import = (
    "from migrations.manager import run_migrations\n"
    "from systems.events import register_event_handlers\n"
)

if "from systems.events import register_event_handlers" not in text:
    if import_marker not in text:
        raise SystemExit(
            "Could not locate migrations import."
        )

    text = text.replace(
        import_marker,
        new_import,
        1,
    )

setup_marker = (
    "    async def setup_hook(self) -> None:\n"
)

setup_insert = (
    "    async def setup_hook(self) -> None:\n"
    "        register_event_handlers()\n"
)

if "        register_event_handlers()\n" not in text:
    if setup_marker not in text:
        raise SystemExit(
            "Could not locate setup_hook."
        )

    text = text.replace(
        setup_marker,
        setup_insert,
        1,
    )

path.write_text(
    text,
    encoding="utf-8",
)

print("Registered Event Bus in bot_v5.py")
