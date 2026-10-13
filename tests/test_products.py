from datetime import date

import pytest

from models import Product
from models.products import (
    add_product,
    change_product_quantity,
    find_product_by_id,
    find_products,
    get_inventory_statistics,
    remove_product,
    sort_products_by_expiry,
)


# создание тестового списка косметических средств
def make_products() -> list[Product]:
    return [
        Product(
            product_id=1,
            name="Тональный крем",
            brand="L'Oreal",
            category="Лицо",
            quantity=1,
            expiry_date=date(2026, 12, 1),
        ),
        Product(
            product_id=2,
            name="Тушь",
            brand="Maybelline",
            category="Глаза",
            quantity=3,
            expiry_date=date(2027, 5, 10),
        ),
    ]


def test_product_creation() -> None:
    product = make_products()[0]
    assert product.id == 1
    assert product.name == "Тональный крем"
    assert product.brand == "L'Oreal"
    assert product.category == "Лицо"
    assert product.quantity == 1
    assert product.expiry_date == date(2026, 12, 1)


def test_product_string_representation() -> None:
    product = make_products()[0]
    assert str(product) == "Лицо | L'Oreal — Тональный крем"


@pytest.mark.parametrize(
    ("expiry_date", "today", "expected"),
    [
        (
            date(2026, 9, 27),
            date(2026, 9, 28),
            "Просрочено! Необходимо утилизировать",
        ),
        (
            date(2026, 10, 10),
            date(2026, 9, 28),
            "Срок годности истекает через 12 дн. Пора заменить",
        ),
        (
            date(2026, 12, 1),
            date(2026, 9, 28),
            "Срок годности в порядке (осталось 64 дн.)",
        ),
    ],
)
def test_product_expiry_status(
    expiry_date: date, today: date, expected: str
) -> None:
    product = Product(1, "Крем", "Librederm", "Лицо", 2, expiry_date)
    assert product.get_expiry_status(today) == expected


@pytest.mark.parametrize(
    ("quantity", "expected"),
    [
        (0, "Средство закончилось"),
        (1, "Заканчивается, стоит добавить в список покупок"),
        (2, "В наличии"),
    ],
)
def test_product_quantity_status(quantity: int, expected: str) -> None:
    product = Product(
        1,
        "Крем",
        "Librederm",
        "Лицо",
        quantity,
        date(2027, 5, 10),
    )
    assert product.get_quantity_status() == expected


@pytest.mark.parametrize(
    ("quantity", "expiry_date", "expected"),
    [
        (1, date(2027, 5, 10), True),
        (3, date(2026, 10, 10), True),
        (3, date(2027, 5, 10), False),
    ],
)
def test_product_restock_rules(
    quantity: int, expiry_date: date, expected: bool
) -> None:
    product = Product(
        1,
        "Крем",
        "Librederm",
        "Лицо",
        quantity,
        expiry_date,
    )
    assert product.needs_restock(date(2026, 9, 28)) is expected


def test_product_change_quantity() -> None:
    product = make_products()[0]
    product.change_quantity(5)
    assert product.quantity == 5


def test_product_rejects_negative_quantity_change() -> None:
    product = make_products()[0]
    with pytest.raises(ValueError):
        product.change_quantity(-1)
    assert product.quantity == 1


@pytest.mark.parametrize(
    ("product_id", "name", "brand", "category", "quantity"),
    [
        (0, "Крем", "Librederm", "Лицо", 1),
        (1, "", "Librederm", "Лицо", 1),
        (1, "Крем", "", "Лицо", 1),
        (1, "Крем", "Librederm", "", 1),
        (1, "Крем", "Librederm", "Лицо", -1),
    ],
)
def test_product_rejects_invalid_data(
    product_id: int,
    name: str,
    brand: str,
    category: str,
    quantity: int,
) -> None:
    with pytest.raises(ValueError):
        Product(
            product_id,
            name,
            brand,
            category,
            quantity,
            date(2027, 5, 10),
        )


def test_product_quantity_validation() -> None:
    assert Product.validate_quantity(0)
    assert Product.validate_quantity(5)
    assert not Product.validate_quantity(-1)


def test_add_product() -> None:
    products = make_products()
    product = add_product(
        products,
        "Шампунь",
        "Estel",
        "Волосы",
        2,
        date(2027, 8, 20),
    )
    assert isinstance(product, Product)
    assert product.id == 3
    assert product.name == "Шампунь"
    assert product.brand == "Estel"
    assert product.category == "Волосы"
    assert product.quantity == 2
    assert product.expiry_date == date(2027, 8, 20)
    assert products[-1] is product


def test_find_products_is_case_insensitive() -> None:
    products = make_products()
    assert find_products(products, "l'oreal") == [products[0]]
    assert find_products(products, "ГЛАЗА") == [products[1]]


def test_find_product_by_id() -> None:
    products = make_products()
    assert find_product_by_id(products, 1) is products[0]
    assert find_product_by_id(products, 100) is None


def test_sort_products_by_expiry() -> None:
    products = make_products()
    sorted_products = sort_products_by_expiry(list(reversed(products)))
    assert [product.id for product in sorted_products] == [1, 2]


def test_change_quantity_and_remove_product() -> None:
    products = make_products()
    change_product_quantity(products, 1, 4)
    removed_product = remove_product(products, 2)
    assert products[0].quantity == 4
    assert removed_product.name == "Тушь"
    assert len(products) == 1


def test_change_quantity_for_unknown_product() -> None:
    with pytest.raises(ValueError):
        change_product_quantity(make_products(), 100, 2)


def test_remove_unknown_product() -> None:
    with pytest.raises(ValueError):
        remove_product(make_products(), 100)


def test_inventory_statistics() -> None:
    statistics = get_inventory_statistics(
        make_products(), date(2026, 9, 28)
    )
    assert statistics == {
        "products_count": 2,
        "total_quantity": 4,
        "categories_count": 2,
        "restock_count": 1,
    }


def test_empty_inventory_statistics() -> None:
    assert get_inventory_statistics([], date(2026, 9, 28)) == {
        "products_count": 0,
        "total_quantity": 0,
        "categories_count": 0,
        "restock_count": 0,
    }
