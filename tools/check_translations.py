from __future__ import annotations

import json
import sys
from pathlib import Path

LOCALES = Path(__file__).resolve().parent.parent / "locales"


def flatten(data, prefix=""):
    result = {}

    for key, value in data.items():
        full = f"{prefix}.{key}" if prefix else key

        if isinstance(value, dict):
            result.update(flatten(value, full))
        else:
            result[full] = value

    return result


def main():
    english = json.loads((LOCALES / "en.json").read_text(encoding="utf-8"))
    english_keys = set(flatten(english))

    failed = False

    for locale in sorted(LOCALES.glob("*.json")):
        if locale.name == "en.json":
            continue

        data = json.loads(locale.read_text(encoding="utf-8"))
        keys = set(flatten(data))

        missing = sorted(english_keys - keys)
        extra = sorted(keys - english_keys)

        if missing or extra:
            failed = True

            print(f"\n{locale.name}")

            if missing:
                print(" Missing:")
                for key in missing:
                    print(f"   - {key}")

            if extra:
                print(" Extra:")
                for key in extra:
                    print(f"   + {key}")

    if failed:
        sys.exit(1)

    print("✓ All translations match English.")


if __name__ == "__main__":
    main()
