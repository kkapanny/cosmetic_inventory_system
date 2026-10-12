from datetime import date

import pytest

from products import (
    add_product,
    change_product_quantity,
    find_products,
    get_inventory_statistics,
    is_need_restock,
    remove_product,
    sort_products_by_expiry,
)


# создание тестового списка косметических средств
def make_products() -> list[dict]:
    return [
        {
            "id": 1,
            "name": "Тональный крем",
            "brand": "L'Oreal",
            "category": "Лицо",
            "quantity": 1,
            "expiry_date": "2026-12-01",
        },
        {
            "id": 2,
            "name": "Тушь",
            "brand": "Maybelline",
            "category": "Глаза",
            "quantity": 3,
            "expiry_date": "2027-05-10",
        },
    ]


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
    assert product["id"] == 3
    assert products[-1]["name"] == "Шампунь"


def test_find_products_is_case_insensitive() -> None:
    products = make_products()
    assert find_products(products, "l'oreal") == [products[0]]
    assert find_products(products, "ГЛАЗА") == [products[1]]


def test_restock_is_needed_for_low_quantity() -> None:
    assert is_need_restock(1, date(2027, 5, 10), date(2026, 9, 28))


def test_sort_products_by_expiry() -> None:
    products = make_products()
    sorted_products = sort_products_by_expiry(list(reversed(products)))
    assert [product["id"] for product in sorted_products] == [1, 2]


def test_change_quantity_and_remove_product() -> None:
    products = make_products()
    change_product_quantity(products, 1, 4)
    removed_product = remove_product(products, 2)
    assert products[0]["quantity"] == 4
    assert removed_product["name"] == "Тушь"
    assert len(products) == 1


def test_change_quantity_for_unknown_product() -> None:
    with pytest.raises(ValueError):
        change_product_quantity(make_products(), 100, 2)


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
