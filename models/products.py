# модель косметического средства

from datetime import date


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
