from migrations.manager import run_migrations


def main() -> None:
    migrations = run_migrations()

    if migrations:
        print("Applied migrations:")
        for migration in migrations:
            print(f"  - {migration}")
    else:
        print("No new migrations to apply.")


if __name__ == "__main__":
    main()
