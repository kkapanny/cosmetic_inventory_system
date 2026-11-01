from pathlib import Path

from db.database import DB_PATH, get_connection, initialize_database
from storage import load_products


BASE_DIR = Path(__file__).resolve().parent.parent
PRODUCTS_FILE = BASE_DIR / "data" / "products.json"


def import_products(
    products_file: str | Path = PRODUCTS_FILE,
    db_path: str | Path = DB_PATH,
) -> None:
    """Перенести продукты из JSON в нормализованные таблицы SQLite."""
    products = load_products(products_file)
    initialize_database(db_path)

    brand_names = sorted({product.brand for product in products})
    category_names = sorted({product.category for product in products})

    with get_connection(db_path) as connection:
        connection.execute("DELETE FROM products")
        connection.execute("DELETE FROM brands")
        connection.execute("DELETE FROM categories")

        connection.executemany(
            "INSERT INTO brands (name) VALUES (?)",
            [(name,) for name in brand_names],
        )
        connection.executemany(
            "INSERT INTO categories (name) VALUES (?)",
            [(name,) for name in category_names],
        )

        brands = {
            row["name"]: row["id"]
            for row in connection.execute("SELECT id, name FROM brands")
        }
        categories = {
            row["name"]: row["id"]
            for row in connection.execute("SELECT id, name FROM categories")
        }

        connection.executemany(
            """
            INSERT INTO products (
                id,
                name,
                brand_id,
                category_id,
                quantity,
                expiry_date
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    product.id,
                    product.name,
                    brands[product.brand],
                    categories[product.category],
                    product.quantity,
                    product.expiry_date.isoformat(),
                )
                for product in products
            ],
        )


def main() -> None:
    import_products()


if __name__ == "__main__":
    main()
