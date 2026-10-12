# точка запуска системы учета косметики

from datetime import date
from pathlib import Path

from products import (
    add_product,
    change_product_quantity,
    find_products,
    format_product_info,
    get_expiry_status,
    get_inventory_statistics,
    get_quantity_status,
    is_need_restock,
    remove_product,
    sort_products_by_expiry,
)
from storage import load_products, save_products
from utils import input_date, input_int


DATA_FILE = Path(__file__).parent / "data" / "products.json"


# вывод списка косметических средств
def show_products(products: list[dict]) -> None:
    if not products:
        print("Список косметических средств пуст.")
        return

    print("\n=== Косметические средства ===")
    for product in products:
        expiry_date = date.fromisoformat(product["expiry_date"])
        product_info = format_product_info(
            product["name"], product["brand"], product["category"]
        )
        print(f'{product["id"]}. {product_info}')
        print(
            f'   Количество: {product["quantity"]} шт. | '
            f'Годен до: {expiry_date:%d.%m.%Y}'
        )
        print(f"   {get_expiry_status(expiry_date, date.today())}")
        print(f'   {get_quantity_status(product["quantity"])}')


# вывод средств для пополнения или замены
def show_restock_list(products: list[dict]) -> None:
    restock_products = [
        product
        for product in products
        if is_need_restock(
            product["quantity"],
            date.fromisoformat(product["expiry_date"]),
            date.today(),
        )
    ]

    if not restock_products:
        print("Пополнение запасов не требуется.")
        return

    print("\n=== Список покупок ===")
    for product in restock_products:
        product_info = format_product_info(
            product["name"], product["brand"], product["category"]
        )
        print(f"- {product_info}")


# вывод краткой статистики по косметическим средствам
def show_statistics(products: list[dict]) -> None:
    statistics = get_inventory_statistics(products, date.today())
    print("\n=== Статистика ===")
    print(f'Позиций: {statistics["products_count"]}')
    print(f'Всего единиц: {statistics["total_quantity"]}')
    print(f'Категорий: {statistics["categories_count"]}')
    print(f'Требуют пополнения или замены: {statistics["restock_count"]}')


# вывод главного меню приложения
def print_menu() -> None:
    print("\n=== Cosmetic Inventory System ===")
    print("1. Показать все средства")
    print("2. Найти средство")
    print("3. Добавить средство")
    print("4. Изменить количество")
    print("5. Удалить средство")
    print("6. Показать список покупок")
    print("7. Сортировать по сроку годности")
    print("8. Показать статистику")
    print("0. Выход")


# запрос данных и добавление косметического средства
def add_product_from_input(products: list[dict]) -> None:
    name = input("Название: ").strip()
    brand = input("Бренд: ").strip()
    category = input("Категория: ").strip()
    quantity = input_int("Количество: ", minimum=0)
    expiry_date = input_date("Срок годности (ДД.ММ.ГГГГ): ")

    try:
        product = add_product(
            products,
            name,
            brand,
            category,
            quantity,
            expiry_date,
        )
    except ValueError as error:
        print(f"Не удалось добавить средство: {error}")
        return

    save_products(DATA_FILE, products)
    print(f'Средство добавлено с идентификатором {product["id"]}.')


# поиск и вывод средств по запросу пользователя
def find_products_from_input(products: list[dict]) -> None:
    query = input("Введите название, бренд или категорию: ")
    found_products = find_products(products, query)
    show_products(found_products)


# запрос нового количества выбранного средства
def change_quantity_from_input(products: list[dict]) -> None:
    product_id = input_int("Идентификатор средства: ", minimum=1)
    quantity = input_int("Новое количество: ", minimum=0)

    try:
        change_product_quantity(products, product_id, quantity)
    except ValueError as error:
        print(error)
        return

    save_products(DATA_FILE, products)
    print("Количество обновлено.")


# удаление выбранного косметического средства
def remove_product_from_input(products: list[dict]) -> None:
    product_id = input_int("Идентификатор средства: ", minimum=1)

    try:
        remove_product(products, product_id)
    except ValueError as error:
        print(error)
        return

    save_products(DATA_FILE, products)
    print("Средство удалено.")


# загрузка данных и запуск цикла главного меню
def main() -> None:
    try:
        products = load_products(DATA_FILE)
    except ValueError as error:
        print(f"Ошибка загрузки данных: {error}")
        return

    actions = {
        1: lambda: show_products(products),
        2: lambda: find_products_from_input(products),
        3: lambda: add_product_from_input(products),
        4: lambda: change_quantity_from_input(products),
        5: lambda: remove_product_from_input(products),
        6: lambda: show_restock_list(products),
        7: lambda: show_products(sort_products_by_expiry(products)),
        8: lambda: show_statistics(products),
    }

    while True:
        print_menu()
        choice = input_int("Выберите действие: ", minimum=0, maximum=8)
        if choice == 0:
            print("Данные сохранены. До свидания!")
            break
        actions[choice]()


if __name__ == "__main__":
    main()
