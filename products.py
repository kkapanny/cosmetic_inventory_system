# функции для работы с косметическими средствами

from datetime import date
from typing import Iterator


# определение статуса срока годности средства
def get_expiry_status(expiry_date: date, today: date) -> str:
    days_left = (expiry_date - today).days
    if days_left < 0:
        return "Просрочено! Необходимо утилизировать"
    if days_left <= 30:
        return f"Срок годности истекает через {days_left} дн. Пора заменить"
    return f"Срок годности в порядке (осталось {days_left} дн.)"


# определение статуса наличия средства
def get_quantity_status(quantity: int) -> str:
    if quantity == 0:
        return "Средство закончилось"
    if quantity == 1:
        return "Заканчивается, стоит добавить в список покупок"
    return "В наличии"


# проверка необходимости пополнения запаса или замены средства
def is_need_restock(quantity: int, expiry_date: date, today: date) -> bool:
    days_left = (expiry_date - today).days
    return quantity <= 1 or days_left <= 30


# формирование строки с информацией о средстве
def format_product_info(name: str, brand: str, category: str) -> str:
    return f"{category} | {brand} — {name}"


# добавление косметического средства и возврат созданной записи
def add_product(
    products: list[dict],
    name: str,
    brand: str,
    category: str,
    quantity: int,
    expiry_date: date,
) -> dict:
    if not name or not brand or not category:
        raise ValueError("Название, бренд и категория не могут быть пустыми.")
    if quantity < 0:
        raise ValueError("Количество не может быть отрицательным.")

    product_id = max((product["id"] for product in products), default=0) + 1
    product = {
        "id": product_id,
        "name": name,
        "brand": brand,
        "category": category,
        "quantity": quantity,
        "expiry_date": expiry_date.isoformat(),
    }
    products.append(product)
    return product


# перебор средств, совпадающих с поисковым запросом
def iter_products_by_query(
    products: list[dict], query: str
) -> Iterator[dict]:
    normalized_query = query.strip().lower()
    for product in products:
        searchable_values = (
            product["name"],
            product["brand"],
            product["category"],
        )
        if any(
            normalized_query in value.lower() for value in searchable_values
        ):
            yield product


# поиск средств по названию, бренду или категории
def find_products(products: list[dict], query: str) -> list[dict]:
    return list(iter_products_by_query(products, query))


# сортировка средств по сроку годности
def sort_products_by_expiry(products: list[dict]) -> list[dict]:
    return sorted(products, key=lambda product: product["expiry_date"])


# изменение количества средства и возврат обновленной записи
def change_product_quantity(
    products: list[dict], product_id: int, quantity: int
) -> dict:
    if quantity < 0:
        raise ValueError("Количество не может быть отрицательным.")

    for product in products:
        if product["id"] == product_id:
            product["quantity"] = quantity
            return product
    raise ValueError(f"Средство с идентификатором {product_id} не найдено.")


# удаление средства по идентификатору и возврат удаленной записи
def remove_product(products: list[dict], product_id: int) -> dict:
    for product in products:
        if product["id"] == product_id:
            products.remove(product)
            return product
    raise ValueError(f"Средство с идентификатором {product_id} не найдено.")


# расчет сводной статистики по косметическим средствам
def get_inventory_statistics(products: list[dict], today: date) -> dict:
    categories = {product["category"] for product in products}
    restock_count = sum(
        is_need_restock(
            product["quantity"],
            date.fromisoformat(product["expiry_date"]),
            today,
        )
        for product in products
    )
    return {
        "products_count": len(products),
        "total_quantity": sum(
            product["quantity"] for product in products
        ),
        "categories_count": len(categories),
        "restock_count": restock_count,
    }
