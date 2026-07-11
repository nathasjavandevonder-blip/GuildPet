from pathlib import Path

FILES = [
    Path("ui/views/combat_view.py"),
    Path("tests/test_v5_gameplay.py"),
    Path("tests/test_v5_combat2.py"),
]

for path in FILES:
    if not path.exists():
        continue

    text = path.read_text(encoding="utf-8")

    text = text.replace(
        "result = perform_action(\n",
        "result = await perform_action(\n",
    )

    path.write_text(
        text,
        encoding="utf-8",
    )

    print(f"Updated {path}")
