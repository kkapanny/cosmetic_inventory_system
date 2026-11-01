import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "cosmetic_inventory.sqlite"
SCHEMA_PATH = BASE_DIR / "sql" / "schema.sql"


def get_connection(db_path: str | Path = DB_PATH) -> sqlite3.Connection:
    """Открыть соединение с базой косметического инвентаря."""
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(
    db_path: str | Path = DB_PATH,
    schema_path: str | Path = SCHEMA_PATH,
) -> None:
    """Создать файл базы данных и применить SQL-схему."""
    database_path = Path(db_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    schema = Path(schema_path).read_text(encoding="utf-8")

    with get_connection(database_path) as connection:
        connection.executescript(schema)
