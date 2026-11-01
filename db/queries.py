import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path
from typing import Sequence

from db.database import DB_PATH, get_connection


PRODUCT_FIELDS = """
    products.id,
    products.name,
    brands.name AS brand,
    categories.name AS category,
    products.quantity,
    products.expiry_date
"""

PRODUCT_RELATIONS = """
FROM products
JOIN brands ON products.brand_id = brands.id
JOIN categories ON products.category_id = categories.id
"""


def fetch_all(
    sql: str,
    parameters: Sequence[object] = (),
    db_path: str | Path = DB_PATH,
) -> list[sqlite3.Row]:
    """Выполнить SELECT и вернуть все строки с доступом по именам."""
    with closing(get_connection(db_path)) as connection:
        return connection.execute(sql, parameters).fetchall()


def fetch_one(
    sql: str,
    parameters: Sequence[object] = (),
    db_path: str | Path = DB_PATH,
) -> sqlite3.Row | None:
    """Выполнить SELECT и вернуть одну строку либо None."""
    with closing(get_connection(db_path)) as connection:
        return connection.execute(sql, parameters).fetchone()


def list_products(
    db_path: str | Path = DB_PATH,
) -> list[sqlite3.Row]:
    sql = f"""
        SELECT {PRODUCT_FIELDS}
        {PRODUCT_RELATIONS}
        ORDER BY products.expiry_date, products.name
    """
    return fetch_all(sql, db_path=db_path)


def get_product(
    product_id: int,
    db_path: str | Path = DB_PATH,
) -> sqlite3.Row | None:
    sql = f"""
        SELECT {PRODUCT_FIELDS}
        {PRODUCT_RELATIONS}
        WHERE products.id = ?
    """
    return fetch_one(sql, (product_id,), db_path)


def search_products(
    query: str,
    db_path: str | Path = DB_PATH,
) -> list[sqlite3.Row]:
    sql = f"""
        SELECT {PRODUCT_FIELDS}
        {PRODUCT_RELATIONS}
        WHERE products.name LIKE ?
           OR brands.name LIKE ?
           OR categories.name LIKE ?
        ORDER BY products.name
    """
    pattern = f"%{query.strip()}%"
    return fetch_all(sql, (pattern, pattern, pattern), db_path)


def list_products_by_category(
    category: str,
    db_path: str | Path = DB_PATH,
) -> list[sqlite3.Row]:
    sql = f"""
        SELECT {PRODUCT_FIELDS}
        {PRODUCT_RELATIONS}
        WHERE categories.name = ?
        ORDER BY products.name
    """
    return fetch_all(sql, (category,), db_path)


def list_low_stock_products(
    maximum_quantity: int = 1,
    db_path: str | Path = DB_PATH,
) -> list[sqlite3.Row]:
    sql = f"""
        SELECT {PRODUCT_FIELDS}
        {PRODUCT_RELATIONS}
        WHERE products.quantity <= ?
        ORDER BY products.quantity, products.name
    """
    return fetch_all(sql, (maximum_quantity,), db_path)


def list_expiring_products(
    deadline: date,
    db_path: str | Path = DB_PATH,
) -> list[sqlite3.Row]:
    sql = f"""
        SELECT {PRODUCT_FIELDS}
        {PRODUCT_RELATIONS}
        WHERE products.expiry_date <= ?
        ORDER BY products.expiry_date, products.name
    """
    return fetch_all(sql, (deadline.isoformat(),), db_path)


def get_inventory_totals(
    db_path: str | Path = DB_PATH,
) -> sqlite3.Row:
    row = fetch_one(
        """
        SELECT
            COUNT(products.id) AS products_count,
            COALESCE(SUM(products.quantity), 0) AS total_quantity,
            COUNT(DISTINCT products.brand_id) AS brands_count,
            COUNT(DISTINCT products.category_id) AS categories_count
        FROM products
        """,
        db_path=db_path,
    )
    if row is None:
        raise RuntimeError("Агрегатный запрос не вернул результат.")
    return row


def get_attention_count(
    deadline: date,
    maximum_quantity: int = 1,
    db_path: str | Path = DB_PATH,
) -> int:
    row = fetch_one(
        """
        SELECT COUNT(products.id) AS attention_count
        FROM products
        WHERE products.quantity <= ?
           OR products.expiry_date <= ?
        """,
        (maximum_quantity, deadline.isoformat()),
        db_path,
    )
    if row is None:
        raise RuntimeError("Агрегатный запрос не вернул результат.")
    return row["attention_count"]


def get_category_statistics(
    db_path: str | Path = DB_PATH,
) -> list[sqlite3.Row]:
    return fetch_all(
        """
        SELECT
            categories.id,
            categories.name AS category,
            COUNT(products.id) AS products_count,
            COALESCE(SUM(products.quantity), 0) AS total_quantity
        FROM categories
        LEFT JOIN products ON categories.id = products.category_id
        GROUP BY categories.id, categories.name
        ORDER BY categories.name
        """,
        db_path=db_path,
    )


def get_brand_statistics(
    db_path: str | Path = DB_PATH,
) -> list[sqlite3.Row]:
    return fetch_all(
        """
        SELECT
            brands.id,
            brands.name AS brand,
            COUNT(products.id) AS products_count,
            COALESCE(SUM(products.quantity), 0) AS total_quantity
        FROM brands
        LEFT JOIN products ON brands.id = products.brand_id
        GROUP BY brands.id, brands.name
        ORDER BY brands.name
        """,
        db_path=db_path,
    )


def list_categories_with_minimum_products(
    minimum_count: int,
    db_path: str | Path = DB_PATH,
) -> list[sqlite3.Row]:
    return fetch_all(
        """
        SELECT
            categories.id,
            categories.name AS category,
            COUNT(products.id) AS products_count
        FROM categories
        JOIN products ON categories.id = products.category_id
        GROUP BY categories.id, categories.name
        HAVING COUNT(products.id) >= ?
        ORDER BY products_count DESC, categories.name
        """,
        (minimum_count,),
        db_path,
    )


def list_brands_with_low_stock(
    maximum_quantity: int = 1,
    db_path: str | Path = DB_PATH,
) -> list[sqlite3.Row]:
    return fetch_all(
        """
        SELECT
            brands.id,
            brands.name AS brand,
            COUNT(products.id) AS low_stock_count
        FROM brands
        JOIN products ON brands.id = products.brand_id
        WHERE products.quantity <= ?
        GROUP BY brands.id, brands.name
        HAVING COUNT(products.id) > 0
        ORDER BY low_stock_count DESC, brands.name
        """,
        (maximum_quantity,),
        db_path,
    )
