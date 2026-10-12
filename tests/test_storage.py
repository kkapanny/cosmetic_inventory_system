import json

import pytest

from storage import load_products, save_products


def test_save_and_load_products(tmp_path) -> None:
    filename = tmp_path / "products.json"
    products = [{"id": 1, "name": "Крем"}]
    save_products(filename, products)
    assert load_products(filename) == products


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
