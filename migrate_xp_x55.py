"""One-time migration for the XP x55 rebalance.

Run once after uploading the new code, before restarting the bot:
    python migrate_xp_x55.py

It multiplies existing dragon XP by 55 so current dragons keep their stage.
It writes a small marker file so it will not run twice by accident.
"""
from pathlib import Path

from database import connect

MARKER = Path(".xp_x55_migrated")

if MARKER.exists():
    print("XP x55 migration already ran. Remove .xp_x55_migrated if you intentionally want to run again.")
    raise SystemExit(0)

con = connect()
cur = con.cursor()
cur.execute("UPDATE dragon SET xp = xp * 55")
con.commit()
con.close()

MARKER.write_text("done\n")
print("Done: existing dragon XP multiplied by 55.")
