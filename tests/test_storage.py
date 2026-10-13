import json
from datetime import date

import pytest

from models import Product
from storage import load_products, save_products


# создание тестового набора данных средства
def make_product_data() -> dict[str, int | str]:
    return {
        "id": 1,
        "name": "Крем",
        "brand": "Librederm",
        "category": "Лицо",
        "quantity": 2,
        "expiry_date": "2027-05-10",
    }


def test_save_and_load_products(tmp_path) -> None:
    filename = tmp_path / "products.json"
    products = [
        Product(
            product_id=1,
            name="Крем",
            brand="Librederm",
            category="Лицо",
            quantity=2,
            expiry_date=date(2027, 5, 10),
        )
    ]
    save_products(filename, products)

    assert json.loads(filename.read_text(encoding="utf-8")) == [
        make_product_data()
    ]

    loaded_products = load_products(filename)
    assert len(loaded_products) == 1
    assert isinstance(loaded_products[0], Product)
    assert loaded_products[0].id == products[0].id
    assert loaded_products[0].name == products[0].name
    assert loaded_products[0].brand == products[0].brand
    assert loaded_products[0].category == products[0].category
    assert loaded_products[0].quantity == products[0].quantity
    assert loaded_products[0].expiry_date == products[0].expiry_date


def test_load_missing_file_returns_empty_list(tmp_path) -> None:
    assert load_products(tmp_path / "missing.json") == []


def test_load_invalid_json(tmp_path) -> None:
    filename = tmp_path / "products.json"
    filename.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError):
        load_products(filename)


def test_load_non_list_json(tmp_path) -> None:
    filename = tmp_path / "products.json"
    filename.write_text(json.dumps({"id": 1}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_products(filename)


def test_load_non_object_product(tmp_path) -> None:
    filename = tmp_path / "products.json"
    filename.write_text(json.dumps([1]), encoding="utf-8")
    with pytest.raises(ValueError):
        load_products(filename)


def test_load_product_with_missing_field(tmp_path) -> None:
    filename = tmp_path / "products.json"
    product_data = make_product_data()
    del product_data["brand"]
    filename.write_text(json.dumps([product_data]), encoding="utf-8")
    with pytest.raises(ValueError):
        load_products(filename)


def test_load_product_with_invalid_expiry_date(tmp_path) -> None:
    filename = tmp_path / "products.json"
    product_data = make_product_data()
    product_data["expiry_date"] = "invalid date"
    filename.write_text(json.dumps([product_data]), encoding="utf-8")
    with pytest.raises(ValueError):
        load_products(filename)


def test_load_product_with_negative_quantity(tmp_path) -> None:
    filename = tmp_path / "products.json"
    product_data = make_product_data()
    product_data["quantity"] = -1
    filename.write_text(json.dumps([product_data]), encoding="utf-8")
    with pytest.raises(ValueError):
        load_products(filename)
