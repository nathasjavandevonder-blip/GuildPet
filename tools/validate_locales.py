from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent

CHECKS = [
    "check_translations.py",
    "check_placeholders.py",
]


def run(script: str) -> None:
    print(f"\n== {script} ==")

    result = subprocess.run(
        [sys.executable, str(TOOLS / script)],
        check=False,
    )

    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    for script in CHECKS:
        run(script)

    print("\n✅ All localization checks passed.")


if __name__ == "__main__":
    main()
