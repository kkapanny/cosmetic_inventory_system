from datetime import date

import pytest
from django.db.models import Avg, Count, Max, Min, Sum
from django.db.models.deletion import ProtectedError

from products.models import Brand, Category, Product


def test_read_filter_exclude_sort_and_limit_queries() -> None:
    assert Product.objects.all().count() == 3
    assert set(
        Product.objects.filter(quantity__lte=1).values_list(
            "pk",
            flat=True,
        )
    ) == {1, 3}
    assert list(
        Product.objects.filter(
            quantity__gte=1,
            expiry_date__lt=date(2027, 1, 1),
        ).values_list("pk", flat=True)
    ) == [1]
    assert list(
        Product.objects.filter(
            brand__name__icontains="oreal",
        ).values_list("pk", flat=True)
    ) == [1]
    assert set(
        Product.objects.exclude(quantity=0).values_list(
            "pk",
            flat=True,
        )
    ) == {1, 2}
    assert list(
        Product.objects.order_by("-quantity").values_list(
            "pk",
            flat=True,
        )
    ) == [2, 1, 3]
    assert list(
        Product.objects.order_by("pk").values_list(
            "pk",
            flat=True,
        )[:2]
    ) == [1, 2]
    assert Product.objects.get(pk=2).name == "Тушь для ресниц"
    with pytest.raises(Product.DoesNotExist):
        Product.objects.get(pk=999)


def test_related_objects_select_related_and_values_queries() -> None:
    product = Product.objects.select_related(
        "brand",
        "category",
    ).get(pk=1)

    assert product.brand.name == "L'Oreal"
    assert product.category.name == "Лицо"
    assert set(product._state.fields_cache) == {"brand", "category"}
    assert list(
        product.brand.products.values_list("name", flat=True)
    ) == ["Тональный крем"]
    assert Product.objects.filter(pk=1).values(
        "name",
        "brand__name",
        "category__name",
    ).get() == {
        "name": "Тональный крем",
        "brand__name": "L'Oreal",
        "category__name": "Лицо",
    }


def test_aggregate_and_annotate_queries() -> None:
    summary = Product.objects.aggregate(
        products_count=Count("pk"),
        total_quantity=Sum("quantity"),
        average_quantity=Avg("quantity"),
        minimum_quantity=Min("quantity"),
        maximum_quantity=Max("quantity"),
    )

    assert summary == {
        "products_count": 3,
        "total_quantity": 3,
        "average_quantity": 1.0,
        "minimum_quantity": 0,
        "maximum_quantity": 2,
    }

    categories = {
        category.name: (
            category.products_count,
            category.total_quantity,
        )
        for category in Category.objects.annotate(
            products_count=Count("products"),
            total_quantity=Sum("products__quantity"),
        )
    }
    brands = {
        brand.name: brand.products_count
        for brand in Brand.objects.annotate(
            products_count=Count("products"),
        )
    }

    assert categories == {
        "Волосы": (1, 0),
        "Глаза": (1, 2),
        "Лицо": (1, 1),
    }
    assert brands == {
        "Estel": 1,
        "L'Oreal": 1,
        "Maybelline": 1,
    }


def test_create_update_and_delete_queries() -> None:
    brand = Brand.objects.create(name="Тестовый бренд")
    category = Category.objects.create(name="Тестовая категория")
    product = Product.objects.create(
        name="Тестовое средство",
        brand=brand,
        category=category,
        quantity=1,
        expiry_date=date(2028, 1, 1),
    )

    try:
        assert Product.objects.filter(pk=product.pk).update(
            quantity=4,
        ) == 1
        product.refresh_from_db()
        assert product.quantity == 4

        with pytest.raises(ProtectedError):
            brand.delete()

        deleted_count, _ = Product.objects.filter(pk=product.pk).delete()
        assert deleted_count == 1
        assert not Product.objects.filter(pk=product.pk).exists()
    finally:
        Product.objects.filter(pk=product.pk).delete()
        brand.delete()
        category.delete()


def test_slug_url_and_generated_stock_flag() -> None:
    product = Product.objects.get(pk=2)
    original_quantity = product.quantity

    try:
        assert product.slug == "tush-dlia-resnits-2"
        assert product.get_absolute_url() == (
            "/products/tush-dlia-resnits-2/"
        )
        assert product.low_stock is False

        product.quantity = 1
        product.save(update_fields=["quantity"])
        product.refresh_from_db()

        assert product.low_stock is True
    finally:
        Product.objects.filter(pk=product.pk).update(
            quantity=original_quantity,
        )


def test_new_product_gets_stable_transliterated_slug() -> None:
    product = Product.objects.create(
        name="Крем для рук",
        brand=Brand.objects.get(name="L'Oreal"),
        category=Category.objects.get(name="Лицо"),
        quantity=1,
        expiry_date=date(2028, 1, 1),
    )

    try:
        assert product.slug == f"krem-dlia-ruk-{product.pk}"
        original_slug = product.slug

        product.name = "Крем для тела"
        product.save()

        assert product.slug == original_slug
    finally:
        product.delete()
