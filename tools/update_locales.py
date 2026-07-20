from __future__ import annotations

import json
from pathlib import Path

LOCALES = Path(__file__).resolve().parent.parent / "locales"

ENGLISH = json.loads(
    (LOCALES / "en.json").read_text(encoding="utf-8")
)


def merge(reference, current):
    if isinstance(reference, dict):
        result = {}

        current = current if isinstance(current, dict) else {}

        for key, value in reference.items():
            result[key] = merge(value, current.get(key))

        return result

    if current is not None:
        return current

    return reference


for locale_file in sorted(LOCALES.glob("*.json")):
    if locale_file.name == "en.json":
        continue

    data = json.loads(locale_file.read_text(encoding="utf-8"))

    merged = merge(ENGLISH, data)

    locale_file.write_text(
        json.dumps(
            merged,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Updated {locale_file.name}")

print("\n✓ All locale files synchronized.")
