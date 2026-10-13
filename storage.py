# сохранение и загрузка данных проекта в формате JSON

import json
from datetime import date
from pathlib import Path

from models import Product


# загрузка списка средств из JSON-файла
def load_products(filename: str | Path) -> list[Product]:
    path = Path(filename)
    try:
        with path.open("r", encoding="utf-8") as file:
            products_data = json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as error:
        raise ValueError("Файл содержит некорректный JSON.") from error
    except OSError as error:
        raise ValueError(f"Не удалось прочитать файл: {error}") from error

    if not isinstance(products_data, list):
        raise ValueError("В JSON-файле должен находиться список средств.")

    products = []
    for product_data in products_data:
        if not isinstance(product_data, dict):
            raise ValueError("Средство в JSON должно быть объектом.")
        try:
            product = Product(
                product_id=product_data["id"],
                name=product_data["name"],
                brand=product_data["brand"],
                category=product_data["category"],
                quantity=product_data["quantity"],
                expiry_date=date.fromisoformat(product_data["expiry_date"]),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                "Файл содержит некорректные данные средства."
            ) from error
        products.append(product)
    return products


# сохранение списка средств в JSON-файл
def save_products(filename: str | Path, products: list[Product]) -> None:
    path = Path(filename)
    products_data = [
        {
            "id": product.id,
            "name": product.name,
            "brand": product.brand,
            "category": product.category,
            "quantity": product.quantity,
            "expiry_date": product.expiry_date.isoformat(),
        }
        for product in products
    ]
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(products_data, file, ensure_ascii=False, indent=4)
    except OSError as error:
        raise ValueError(f"Не удалось сохранить файл: {error}") from error
