import argparse
import os
import sqlite3
import sys
from datetime import date
from pathlib import Path

import django
from django.db import transaction


BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_DB = BASE_DIR / "data" / "cosmetic_inventory.sqlite"
REQUIRED_TABLES = {"brands", "categories", "products"}


def read_source_inventory(
    source_db: str | Path,
) -> tuple[list[sqlite3.Row], list[sqlite3.Row], list[sqlite3.Row]]:
    database_path = Path(source_db).resolve()
    if not database_path.is_file():
        raise FileNotFoundError(
            f"Исходная база не найдена: {database_path}"
        )

    database_uri = f"{database_path.as_uri()}?mode=ro"
    with sqlite3.connect(database_uri, uri=True) as connection:
        connection.row_factory = sqlite3.Row
        tables = {
            row["name"]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name NOT LIKE 'sqlite_%'
                """
            )
        }
        missing_tables = REQUIRED_TABLES - tables
        if missing_tables:
            missing = ", ".join(sorted(missing_tables))
            raise ValueError(
                f"В исходной базе отсутствуют таблицы: {missing}"
            )

        brands = connection.execute(
            "SELECT id, name FROM brands ORDER BY id"
        ).fetchall()
        categories = connection.execute(
            "SELECT id, name FROM categories ORDER BY id"
        ).fetchall()
        products = connection.execute(
            """
            SELECT
                id,
                name,
                brand_id,
                category_id,
                quantity,
                expiry_date
            FROM products
            ORDER BY id
            """
        ).fetchall()

    validate_source_inventory(brands, categories, products)
    return brands, categories, products


def validate_source_inventory(
    brands: list[sqlite3.Row],
    categories: list[sqlite3.Row],
    products: list[sqlite3.Row],
) -> None:
    brand_ids = {row["id"] for row in brands}
    category_ids = {row["id"] for row in categories}
    missing_brands = {
        row["brand_id"] for row in products
    } - brand_ids
    missing_categories = {
        row["category_id"] for row in products
    } - category_ids

    if missing_brands:
        raise ValueError(
            "Товары ссылаются на несуществующие бренды: "
            f"{sorted(missing_brands)}"
        )
    if missing_categories:
        raise ValueError(
            "Товары ссылаются на несуществующие категории: "
            f"{sorted(missing_categories)}"
        )

    for product in products:
        if product["quantity"] < 0:
            raise ValueError(
                "Количество товара не может быть отрицательным: "
                f"id={product['id']}"
            )
        date.fromisoformat(product["expiry_date"])


def import_inventory(source_db: str | Path = SOURCE_DB) -> dict[str, int]:
    brands, categories, products = read_source_inventory(source_db)

    sys.path.insert(0, str(BASE_DIR))
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "cosmetic_inventory.settings",
    )
    django.setup()

    from products.models import Brand, Category, Product

    with transaction.atomic():
        for row in brands:
            Brand.objects.update_or_create(
                pk=row["id"],
                defaults={"name": row["name"]},
            )

        for row in categories:
            Category.objects.update_or_create(
                pk=row["id"],
                defaults={"name": row["name"]},
            )

        for row in products:
            Product.objects.update_or_create(
                pk=row["id"],
                defaults={
                    "name": row["name"],
                    "brand_id": row["brand_id"],
                    "category_id": row["category_id"],
                    "quantity": row["quantity"],
                    "expiry_date": date.fromisoformat(
                        row["expiry_date"]
                    ),
                },
            )

    return {
        "brands": len(brands),
        "categories": len(categories),
        "products": len(products),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Перенести данные ПР7 в таблицы Django ORM.",
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
    counts = import_inventory(args.source_db)
    print("Перенос данных завершён.")
    print(f"Брендов: {counts['brands']}")
    print(f"Категорий: {counts['categories']}")
    print(f"Средств: {counts['products']}")


if __name__ == "__main__":
    main()
