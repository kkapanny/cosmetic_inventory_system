import json
from datetime import date

import pytest

from models import Product
from storage import load_products, save_products


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
    loaded_products = load_products(filename)
    assert len(loaded_products) == 1
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
