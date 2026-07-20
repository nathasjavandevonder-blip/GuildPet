from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

LOCALES = Path(__file__).resolve().parent.parent / "locales"

if len(sys.argv) < 4:
    print("Usage:")
    print("python3 tools/create_locale.py <locale> <English Name> <Native Name>")
    sys.exit(1)

locale = sys.argv[1]
english_name = sys.argv[2]
native_name = " ".join(sys.argv[3:])

destination = LOCALES / f"{locale}.json"

if destination.exists():
    print(f"{destination.name} already exists.")
    sys.exit(1)

shutil.copy2(
    LOCALES / "en.json",
    destination,
)

data = json.loads(destination.read_text(encoding="utf-8"))

data["meta"]["name"] = english_name
data["meta"]["native_name"] = native_name

destination.write_text(
    json.dumps(
        data,
        indent=2,
        ensure_ascii=False,
    ) + "\n",
    encoding="utf-8",
)

print(f"Created {destination.name}")
