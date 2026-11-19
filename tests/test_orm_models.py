import os
from datetime import date

import django
from django.db import models


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "cosmetic_inventory.settings",
)
django.setup()


def make_product(quantity: int = 1):
    from products.models import Brand, Category, Product

    return Product(
        name="Тональный крем",
        brand=Brand(name="L'Oreal"),
        category=Category(name="Лицо"),
        quantity=quantity,
        expiry_date=date(2026, 12, 1),
    )


def test_inventory_models_have_expected_fields() -> None:
    from products.models import Brand, Category, Product

    assert isinstance(Brand._meta.get_field("name"), models.CharField)
    assert Brand._meta.get_field("name").unique is True
    assert isinstance(Category._meta.get_field("name"), models.CharField)
    assert Category._meta.get_field("name").unique is True

    assert isinstance(Product._meta.get_field("name"), models.CharField)
    assert isinstance(
        Product._meta.get_field("quantity"),
        models.PositiveIntegerField,
    )
    assert isinstance(
        Product._meta.get_field("expiry_date"),
        models.DateField,
    )
    assert isinstance(
        Product._meta.get_field("low_stock"),
        models.GeneratedField,
    )
    assert Product._meta.get_field("slug").unique is True


def test_product_foreign_keys_protect_related_records() -> None:
    from products.models import Brand, Category, Product

    brand_field = Product._meta.get_field("brand")
    category_field = Product._meta.get_field("category")

    assert brand_field.remote_field.model is Brand
    assert brand_field.remote_field.on_delete is models.PROTECT
    assert brand_field.remote_field.related_name == "products"
    assert category_field.remote_field.model is Category
    assert category_field.remote_field.on_delete is models.PROTECT
    assert category_field.remote_field.related_name == "products"


def test_models_have_readable_string_representations() -> None:
    product = make_product()

    assert str(product.brand) == "L'Oreal"
    assert str(product.category) == "Лицо"
    assert str(product) == "Лицо | L'Oreal — Тональный крем"


def test_product_preserves_inventory_status_rules() -> None:
    product = make_product(quantity=1)

    assert product.get_quantity_status() == (
        "Заканчивается, стоит добавить в список покупок"
    )
    assert product.get_expiry_status(date(2026, 11, 1)) == (
        "Срок годности истекает через 30 дн. Пора заменить"
    )
    assert product.needs_restock(date(2026, 11, 1)) is True


def test_product_rejects_negative_quantity_change() -> None:
    product = make_product()

    try:
        product.change_quantity(-1)
    except ValueError as error:
        assert str(error) == "Количество не может быть отрицательным."
    else:
        raise AssertionError("Отрицательное количество должно быть отклонено")

    assert product.quantity == 1
