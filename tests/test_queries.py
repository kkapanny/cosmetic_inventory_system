from datetime import date
from pathlib import Path

import pytest

from db.database import get_connection
from db.import_json import import_products
from db.queries import (
    get_attention_count,
    get_brand_statistics,
    get_category_statistics,
    get_inventory_totals,
    get_product,
    list_brands_with_low_stock,
    list_categories_with_minimum_products,
    list_expiring_products,
    list_low_stock_products,
    list_products,
    list_products_by_category,
    search_products,
)


BASE_DIR = Path(__file__).resolve().parent.parent
QUERIES_FILE = BASE_DIR / "sql" / "queries.sql"


@pytest.fixture
def inventory_db(tmp_path):
    database_path = tmp_path / "inventory.sqlite"
    import_products(db_path=database_path)
    return database_path


def test_queries_file_contains_twelve_executable_queries(
    inventory_db,
) -> None:
    statements = [
        statement.strip()
        for statement in QUERIES_FILE.read_text(encoding="utf-8").split(";")
        if statement.strip()
    ]
    parameters = [
        (),
        (1,),
        ("%крем%", "%крем%", "%крем%", "", ""),
        ("Лицо",),
        (1,),
        ("2027-01-01",),
        (),
        (1, "2027-01-01"),
        (),
        (),
        (1,),
        (1,),
    ]

    with get_connection(inventory_db) as connection:
        results = [
            connection.execute(statement, values).fetchall()
            for statement, values in zip(
                statements,
                parameters,
                strict=True,
            )
        ]

    assert len(statements) == 12
    assert all(isinstance(result, list) for result in results)


def test_list_products_returns_joined_data(inventory_db) -> None:
    products = list_products(inventory_db)

    assert [product["id"] for product in products] == [1, 2, 3]
    assert dict(products[0]) == {
        "id": 1,
        "name": "Тональный крем",
        "brand": "L'Oreal",
        "category": "Лицо",
        "quantity": 1,
        "expiry_date": "2026-12-01",
    }


def test_get_product_filters_by_identifier(inventory_db) -> None:
    product = get_product(2, inventory_db)

    assert product["name"] == "Тушь для ресниц"
    assert product["brand"] == "Maybelline"
    assert get_product(999, inventory_db) is None


@pytest.mark.parametrize(
    ("query", "expected_ids"),
    [
        ("Тушь", [2]),
        ("ESTEL", [3]),
        ("Лицо", [1]),
        ("несуществующее", []),
    ],
)
def test_search_products_uses_three_fields(
    inventory_db, query, expected_ids
) -> None:
    products = search_products(query, inventory_db)
    assert [product["id"] for product in products] == expected_ids


def test_search_products_treats_input_as_parameter(inventory_db) -> None:
    products = search_products("' OR 1 = 1 --", inventory_db)
    assert products == []


def test_category_and_stock_filters(inventory_db) -> None:
    category_products = list_products_by_category("Глаза", inventory_db)
    low_stock_products = list_low_stock_products(1, inventory_db)

    assert [product["id"] for product in category_products] == [2]
    assert [product["id"] for product in low_stock_products] == [3, 1]


def test_expiry_filter_uses_iso_date_order(inventory_db) -> None:
    products = list_expiring_products(date(2027, 1, 1), inventory_db)
    assert [product["id"] for product in products] == [1]


def test_inventory_aggregates(inventory_db) -> None:
    totals = get_inventory_totals(inventory_db)
    attention_count = get_attention_count(
        date(2027, 1, 1),
        maximum_quantity=1,
        db_path=inventory_db,
    )

    assert dict(totals) == {
        "products_count": 3,
        "total_quantity": 3,
        "brands_count": 3,
        "categories_count": 3,
    }
    assert attention_count == 2


def test_grouped_statistics(inventory_db) -> None:
    category_statistics = get_category_statistics(inventory_db)
    brand_statistics = get_brand_statistics(inventory_db)

    assert [dict(row) for row in category_statistics] == [
        {
            "id": 1,
            "category": "Волосы",
            "products_count": 1,
            "total_quantity": 0,
        },
        {
            "id": 2,
            "category": "Глаза",
            "products_count": 1,
            "total_quantity": 2,
        },
        {
            "id": 3,
            "category": "Лицо",
            "products_count": 1,
            "total_quantity": 1,
        },
    ]
    assert {row["brand"] for row in brand_statistics} == {
        "Estel",
        "L'Oreal",
        "Maybelline",
    }


def test_having_queries_filter_groups(inventory_db) -> None:
    all_categories = list_categories_with_minimum_products(1, inventory_db)
    no_categories = list_categories_with_minimum_products(2, inventory_db)
    low_stock_brands = list_brands_with_low_stock(1, inventory_db)

    assert len(all_categories) == 3
    assert no_categories == []
    assert {row["brand"] for row in low_stock_brands} == {
        "Estel",
        "L'Oreal",
    }
