# модель косметического средства

from datetime import date
from typing import Iterator


class Product:
    # создание объекта косметического средства
    def __init__(
        self,
        product_id: int,
        name: str,
        brand: str,
        category: str,
        quantity: int,
        expiry_date: date,
    ) -> None:
        if product_id < 1:
            raise ValueError("Идентификатор должен быть положительным.")
        if not name or not brand or not category:
            raise ValueError(
                "Название, бренд и категория не могут быть пустыми."
            )
        if not self.validate_quantity(quantity):
            raise ValueError("Количество не может быть отрицательным.")

        self.id = product_id
        self.name = name
        self.brand = brand
        self.category = category
        self.quantity = quantity
        self.expiry_date = expiry_date

    # проверка корректности количества средства
    @staticmethod
    def validate_quantity(quantity: int) -> bool:
        return quantity >= 0

    # определение статуса срока годности средства
    def get_expiry_status(self, today: date) -> str:
        days_left = (self.expiry_date - today).days
        if days_left < 0:
            return "Просрочено! Необходимо утилизировать"
        if days_left <= 30:
            return (
                f"Срок годности истекает через {days_left} дн. "
                "Пора заменить"
            )
        return f"Срок годности в порядке (осталось {days_left} дн.)"

    # определение статуса наличия средства
    def get_quantity_status(self) -> str:
        if self.quantity == 0:
            return "Средство закончилось"
        if self.quantity == 1:
            return "Заканчивается, стоит добавить в список покупок"
        return "В наличии"

    # проверка необходимости пополнения запаса или замены средства
    def needs_restock(self, today: date) -> bool:
        days_left = (self.expiry_date - today).days
        return self.quantity <= 1 or days_left <= 30

    # изменение количества средства
    def change_quantity(self, quantity: int) -> None:
        if not self.validate_quantity(quantity):
            raise ValueError("Количество не может быть отрицательным.")
        self.quantity = quantity

    # формирование строкового представления средства
    def __str__(self) -> str:
        return f"{self.category} | {self.brand} — {self.name}"


# добавление косметического средства в коллекцию
def add_product(
    products: list[Product],
    name: str,
    brand: str,
    category: str,
    quantity: int,
    expiry_date: date,
) -> Product:
    product_id = max((product.id for product in products), default=0) + 1
    product = Product(
        product_id=product_id,
        name=name,
        brand=brand,
        category=category,
        quantity=quantity,
        expiry_date=expiry_date,
    )
    products.append(product)
    return product


# перебор средств, совпадающих с поисковым запросом
def iter_products_by_query(
    products: list[Product], query: str
) -> Iterator[Product]:
    normalized_query = query.strip().lower()
    for product in products:
        searchable_values = (
            product.name,
            product.brand,
            product.category,
        )
        if any(
            normalized_query in value.lower() for value in searchable_values
        ):
            yield product


# поиск средств по названию, бренду или категории
def find_products(
    products: list[Product], query: str
) -> list[Product]:
    return list(iter_products_by_query(products, query))


# сортировка средств по сроку годности
def sort_products_by_expiry(
    products: list[Product],
) -> list[Product]:
    return sorted(products, key=lambda product: product.expiry_date)


# изменение количества средства в коллекции
def change_product_quantity(
    products: list[Product], product_id: int, quantity: int
) -> Product:
    for product in products:
        if product.id == product_id:
            product.change_quantity(quantity)
            return product
    raise ValueError(f"Средство с идентификатором {product_id} не найдено.")


# удаление средства из коллекции по идентификатору
def remove_product(
    products: list[Product], product_id: int
) -> Product:
    for product in products:
        if product.id == product_id:
            products.remove(product)
            return product
    raise ValueError(f"Средство с идентификатором {product_id} не найдено.")


# расчет сводной статистики по косметическим средствам
def get_inventory_statistics(
    products: list[Product], today: date
) -> dict[str, int]:
    categories = {product.category for product in products}
    return {
        "products_count": len(products),
        "total_quantity": sum(product.quantity for product in products),
        "categories_count": len(categories),
        "restock_count": sum(
            product.needs_restock(today) for product in products
        ),
    }
