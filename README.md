# Guild Dragon Bot v3.1 Database Core

## What this fixes

This release fixes the shop crash:

```text
sqlite3.OperationalError: database is locked
```

The bug happened when `shop.py` bought an item and then `memories.py` opened a second SQLite writer while the first transaction was still open.

## New database layer

- WAL mode
- SQLite busy timeout
- Retry helper for temporary locks
- Shared transaction helper
- `add_memory_tx()` for writing memories inside existing transactions
- Shop purchase now writes the memory inside the same transaction

## Also included

- v3 Foundation project structure
- Guild command sync in `on_ready`
- `.gitignore` cleanup

## Update

Upload all files to GitHub, commit, push.

On VPS:

```bash
cd ~/bot/dragonbot
git pull
python -m py_compile bot.py
sudo systemctl restart dragonbot
journalctl -u dragonbot -n 80 --no-pager
```

Then test buying Moss Nest again.

You should see:

```text
Synced X commands to guild: ...
```
