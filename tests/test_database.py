import sqlite3

import pytest

from db.database import get_connection, initialize_database
from db.import_json import import_products


@pytest.fixture
def inventory_db(tmp_path):
    database_path = tmp_path / "inventory.sqlite"
    initialize_database(database_path)
    return database_path


def test_schema_creates_inventory_tables(inventory_db) -> None:
    with get_connection(inventory_db) as connection:
        tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        product_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(products)")
        }

    assert {"brands", "categories", "products"} <= tables
    assert product_columns == {
        "id",
        "name",
        "brand_id",
        "category_id",
        "quantity",
        "expiry_date",
    }


def test_products_table_has_foreign_keys(inventory_db) -> None:
    with get_connection(inventory_db) as connection:
        foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(products)"
        ).fetchall()

    assert {row["table"] for row in foreign_keys} == {
        "brands",
        "categories",
    }


def test_connection_uses_named_rows_and_foreign_keys(inventory_db) -> None:
    with get_connection(inventory_db) as connection:
        row = connection.execute("SELECT 1 AS value").fetchone()
        foreign_keys_enabled = connection.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]

    assert row["value"] == 1
    assert foreign_keys_enabled == 1


def test_import_moves_json_data_and_is_repeatable(inventory_db) -> None:
    import_products(db_path=inventory_db)
    import_products(db_path=inventory_db)

    with get_connection(inventory_db) as connection:
        counts = {
            table: connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            for table in ("brands", "categories", "products")
        }
        product = connection.execute(
            """
            SELECT
                products.name,
                brands.name AS brand,
                categories.name AS category,
                products.quantity,
                products.expiry_date
            FROM products
            JOIN brands ON products.brand_id = brands.id
            JOIN categories ON products.category_id = categories.id
            WHERE products.id = ?
            """,
            (1,),
        ).fetchone()

    assert counts == {"brands": 3, "categories": 3, "products": 3}
    assert dict(product) == {
        "name": "Тональный крем",
        "brand": "L'Oreal",
        "category": "Лицо",
        "quantity": 1,
        "expiry_date": "2026-12-01",
    }


def test_foreign_keys_reject_unknown_relations(inventory_db) -> None:
    with get_connection(inventory_db) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO products (
                    id,
                    name,
                    brand_id,
                    category_id,
                    quantity,
                    expiry_date
                )
                VALUES (1, 'Крем', 999, 999, 1, '2027-01-01')
                """
            )
