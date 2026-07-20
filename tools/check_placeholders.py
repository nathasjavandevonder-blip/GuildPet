from __future__ import annotations

import json
import re
import sys
from pathlib import Path

LOCALES = Path(__file__).resolve().parent.parent / "locales"

PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z0-9_]+)\}")


def flatten(data, prefix=""):
    result = {}

    for key, value in data.items():
        full = f"{prefix}.{key}" if prefix else key

        if isinstance(value, dict):
            result.update(flatten(value, full))
        elif isinstance(value, str):
            result[full] = value

    return result


english = flatten(
    json.loads(
        (LOCALES / "en.json").read_text(encoding="utf-8")
    )
)

failed = False

for locale in sorted(LOCALES.glob("*.json")):
    if locale.name == "en.json":
        continue

    translated = flatten(
        json.loads(locale.read_text(encoding="utf-8"))
    )

    for key, english_text in english.items():
        if key not in translated:
            continue

        en_placeholders = set(
            PLACEHOLDER_RE.findall(english_text)
        )

        tr_placeholders = set(
            PLACEHOLDER_RE.findall(translated[key])
        )

        if en_placeholders != tr_placeholders:
            failed = True

            print(
                f"{locale.name}: {key}"
            )
            print(
                f"  expected: {sorted(en_placeholders)}"
            )
            print(
                f"  found:    {sorted(tr_placeholders)}"
            )
            print()

if failed:
    sys.exit(1)

print("✓ All placeholders are valid.")
