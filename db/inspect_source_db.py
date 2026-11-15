import argparse
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_DB = BASE_DIR / "data" / "cosmetic_inventory.sqlite"


def inspect_database(source_db: str | Path = SOURCE_DB) -> None:
    database_path = Path(source_db).resolve()
    if not database_path.is_file():
        raise FileNotFoundError(
            f"Исходная база не найдена: {database_path}"
        )

    database_uri = f"{database_path.as_uri()}?mode=ro"
    with sqlite3.connect(database_uri, uri=True) as connection:
        connection.row_factory = sqlite3.Row
        tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        for table in tables:
            table_name = table["name"]
            columns = connection.execute(
                f'PRAGMA table_info("{table_name}")'
            ).fetchall()
            count = connection.execute(
                f'SELECT COUNT(*) FROM "{table_name}"'
            ).fetchone()[0]

            print(f"\nТаблица: {table_name}")
            print("Столбцы:")
            for column in columns:
                print(
                    f"  имя={column['name']}, "
                    f"тип={column['type']}, "
                    f"NOT NULL={column['notnull']}, "
                    f"PRIMARY KEY={column['pk']}"
                )
            print(f"Количество записей: {count}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Показать структуру исходной SQLite-базы ПР7.",
    )
    parser.add_argument(
        "source_db",
        nargs="?",
        type=Path,
        default=SOURCE_DB,
        help="путь к исходной SQLite-базе",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    inspect_database(args.source_db)


if __name__ == "__main__":
    main()
