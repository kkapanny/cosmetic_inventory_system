import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from products.admin import (
    BrandProductInline,
    CategoryProductInline,
    ProductAdmin,
)
from products.models import Brand, Category, Product


@pytest.fixture
def admin_client():
    user = get_user_model().objects.create_superuser(
        username="admin-test",
        email="admin@example.com",
        password="test-password",
    )
    client = Client(HTTP_HOST="localhost")
    client.force_login(user)
    yield client
    user.delete()


def test_inventory_models_are_registered_in_admin() -> None:
    assert admin.site.is_registered(Brand)
    assert admin.site.is_registered(Category)
    assert admin.site.is_registered(Product)
    assert Product._meta.app_config.verbose_name == (
        "Косметический инвентарь"
    )


def test_product_admin_configuration() -> None:
    product_admin = admin.site._registry[Product]

    assert isinstance(product_admin, ProductAdmin)
    assert product_admin.search_fields == (
        "name",
        "brand__name",
        "category__name",
    )
    assert product_admin.list_filter == (
        "low_stock",
        "brand",
        "category",
        "expiry_date",
    )
    assert product_admin.list_editable == ("quantity",)
    assert product_admin.list_select_related == ("brand", "category")
    assert product_admin.list_per_page == 25
    assert product_admin.view_on_site is True
    assert "low_stock" in product_admin.readonly_fields


def test_related_products_are_available_as_inlines() -> None:
    brand_admin = admin.site._registry[Brand]
    category_admin = admin.site._registry[Category]

    assert brand_admin.inlines == (BrandProductInline,)
    assert category_admin.inlines == (CategoryProductInline,)


def test_admin_product_search_and_filter(admin_client: Client) -> None:
    url = reverse("admin:products_product_changelist")

    search_response = admin_client.get(url, {"q": "Maybelline"})
    filter_response = admin_client.get(
        url,
        {"category__id__exact": Category.objects.get(name="Лицо").pk},
    )

    assert search_response.status_code == 200
    assert search_response.context["cl"].result_count == 1
    assert filter_response.status_code == 200
    assert filter_response.context["cl"].result_count == 1


def test_admin_can_restock_selected_products(admin_client: Client) -> None:
    url = reverse("admin:products_product_changelist")
    original_quantities = dict(
        Product.objects.filter(pk__in=(1, 3)).values_list(
            "pk",
            "quantity",
        )
    )

    try:
        response = admin_client.post(
            url,
            {
                "action": "restock_selected",
                "_selected_action": [1, 3],
            },
            follow=True,
        )

        assert response.status_code == 200
        assert set(
            Product.objects.filter(
                pk__in=(1, 3),
                quantity=2,
            ).values_list("pk", flat=True)
        ) == {1, 3}
    finally:
        for product_id, quantity in original_quantities.items():
            Product.objects.filter(pk=product_id).update(
                quantity=quantity,
            )
