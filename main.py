from datetime import date

# Данные о косметическом средстве
product_name = "Тональный крем"
brand = "L'Oreal"
category = "Лицо"
quantity = 1
expiry_date = date(2026, 12, 1)
today = date.today()


def get_expiry_status(expiry_date, today):
    """Определяет статус срока годности средства"""
    days_left = (expiry_date - today).days
    if days_left < 0:
        return "Просрочено! Необходимо утилизировать"
    elif days_left <= 30:
        return f"Срок годности истекает через {days_left} дн. Пора заменить"
    return f"Срок годности в порядке (осталось {days_left} дн.)"


def get_quantity_status(quantity):
    """Определяет статус наличия средства"""
    if quantity == 0:
        return "Средство закончилось"
    elif quantity == 1:
        return "Заканчивается, стоит добавить в список покупок"
    return "В наличии"


def is_need_restock(quantity, expiry_date, today):
    """Проверяет, нужно ли пополнить запас"""
    days_left = (expiry_date - today).days
    if quantity <= 1 or days_left <= 30:
        return True
    return False


def format_product_info(name, brand, category):
    """Формирует строку с информацией о средстве"""
    return f"{category} | {brand} — {name}"


# Вывод информации о средстве
print("=" * 40)
print("Информация о косметическом средстве")
print("=" * 40)
print(f"Средство: {format_product_info(product_name, brand, category)}")
print(f"Количество: {quantity} шт.")
print(f"Срок годности до: {expiry_date}")
print("-" * 40)
print(get_expiry_status(expiry_date, today))
print(get_quantity_status(quantity))

if is_need_restock(quantity, expiry_date, today):
    print(">>> Добавлено в список покупок")
else:
    print(">>> Пополнение не требуется")
print("=" * 40)
