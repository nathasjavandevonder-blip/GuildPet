from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable

from core.database import db_session

MigrationFunction = Callable[[], None]


def ensure_migration_table() -> None:
    with db_session() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                migration_name TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def applied_migrations() -> set[str]:
    ensure_migration_table()

    with db_session() as connection:
        rows = connection.execute(
            "SELECT migration_name FROM schema_migrations"
        ).fetchall()

    return {row["migration_name"] for row in rows}


def discover_migrations() -> list[tuple[str, MigrationFunction]]:
    found: list[tuple[str, MigrationFunction]] = []

    package = importlib.import_module("migrations")

    for module_info in pkgutil.iter_modules(package.__path__):
        if not module_info.name.startswith("v5_"):
            continue

        module = importlib.import_module(
            f"migrations.{module_info.name}"
        )
        upgrade = getattr(module, "upgrade", None)

        if callable(upgrade):
            found.append((module_info.name, upgrade))

    return sorted(found, key=lambda item: item[0])


def run_migrations() -> list[str]:
    completed = applied_migrations()
    newly_applied: list[str] = []

    for migration_name, upgrade in discover_migrations():
        if migration_name in completed:
            continue

        upgrade()

        with db_session() as connection:
            connection.execute(
                """
                INSERT INTO schema_migrations (migration_name)
                VALUES (?)
                """,
                (migration_name,),
            )

        newly_applied.append(migration_name)

    return newly_applied
