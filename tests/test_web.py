import inspect
import tempfile
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.staticfiles import finders
from django.db import connection
from django.template.loader import render_to_string
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils.timezone import localdate
from PIL import Image

from products.models import Brand, Category, Product


FIXED_TODAY = date(2026, 11, 1)


# создание тестового HTTP-клиента
def make_client() -> Client:
    return Client(HTTP_HOST="localhost")


def make_product_image() -> SimpleUploadedFile:
    image_bytes = BytesIO()
    Image.new("RGB", (2, 2), "white").save(image_bytes, format="PNG")
    return SimpleUploadedFile(
        "product.png",
        image_bytes.getvalue(),
        content_type="image/png",
    )


def test_named_routes() -> None:
    assert reverse("homepage:index") == "/"
    assert reverse("products:list") == "/products/"
    assert reverse("products:attention") == "/products/attention/"
    assert reverse("products:statistics") == "/products/statistics/"
    assert reverse("products:create") == "/products/create/"
    assert reverse(
        "products:update",
        args=["tonalnyi-krem-1"],
    ) == "/products/tonalnyi-krem-1/edit/"
    assert reverse(
        "products:delete",
        args=["tonalnyi-krem-1"],
    ) == "/products/tonalnyi-krem-1/delete/"
    assert reverse(
        "products:detail",
        args=["tonalnyi-krem-1"],
    ) == "/products/tonalnyi-krem-1/"


def test_product_create_page_displays_modelform() -> None:
    response = make_client().get(reverse("products:create"))
    html = response.content.decode()

    assert response.status_code == 200
    assert response.templates[0].name == "products/form.html"
    assert response.context["form"].is_bound is False
    assert "Добавить средство" in html
    assert 'name="csrfmiddlewaretoken"' in html
    assert 'name="expiry_date"' in html
    assert 'type="date"' in html
    assert 'enctype="multipart/form-data"' in html
    assert 'name="image"' in html


def test_product_create_saves_uploaded_image() -> None:
    brand = Brand.objects.get(name="Maybelline")
    category = Category.objects.get(name="Глаза")

    with tempfile.TemporaryDirectory() as media_root:
        with override_settings(MEDIA_ROOT=media_root):
            response = make_client().post(
                reverse("products:create"),
                {
                    "name": "Крем с изображением",
                    "brand": brand.pk,
                    "category": category.pk,
                    "quantity": 2,
                    "expiry_date": localdate() + timedelta(days=180),
                    "image": make_product_image(),
                },
            )
            product = Product.objects.get(name="Крем с изображением")

            try:
                assert response.status_code == 302
                assert product.image.name.startswith("products/")
                assert Path(media_root, product.image.name).is_file()
            finally:
                product.delete()


def test_product_create_saves_valid_post_and_redirects() -> None:
    brand = Brand.objects.get(name="Maybelline")
    category = Category.objects.get(name="Глаза")
    response = make_client().post(
        reverse("products:create"),
        {
            "name": "Карандаш для глаз",
            "brand": brand.pk,
            "category": category.pk,
            "quantity": 3,
            "expiry_date": localdate() + timedelta(days=180),
        },
    )
    product = Product.objects.get(name="Карандаш для глаз")

    try:
        assert response.status_code == 302
        assert response.url == product.get_absolute_url()
    finally:
        product.delete()


def test_product_create_shows_errors_without_saving() -> None:
    brand = Brand.objects.get(name="Estel")
    category = Category.objects.get(name="Волосы")
    products_before = Product.objects.count()
    response = make_client().post(
        reverse("products:create"),
        {
            "name": "Просроченный кондиционер",
            "brand": brand.pk,
            "category": category.pk,
            "quantity": 1,
            "expiry_date": localdate() - timedelta(days=1),
        },
    )
    html = response.content.decode()

    assert response.status_code == 200
    assert Product.objects.count() == products_before
    assert "Срок годности не может быть в прошлом" in html
    assert "Просроченный кондиционер" in html
    assert 'id="id_expiry_date_helptext"' in html
    assert 'id="id_expiry_date_error"' in html


def test_product_create_rejects_post_without_csrf_token() -> None:
    response = Client(
        HTTP_HOST="localhost",
        enforce_csrf_checks=True,
    ).post(reverse("products:create"), {})

    assert response.status_code == 403


def test_product_create_escapes_bound_values() -> None:
    response = make_client().post(
        reverse("products:create"),
        {
            "name": "<script>alert('test')</script>",
            "quantity": 0,
            "expiry_date": localdate() + timedelta(days=30),
        },
    )
    html = response.content.decode()

    assert response.status_code == 200
    assert "&lt;script&gt;alert(&#x27;test&#x27;)&lt;/script&gt;" in html
    assert "<script>alert('test')</script>" not in html


def test_product_update_page_uses_existing_instance() -> None:
    product = Product.objects.get(name="Тушь для ресниц")
    response = make_client().get(
        reverse("products:update", args=[product.slug])
    )
    html = response.content.decode()

    assert response.status_code == 200
    assert response.templates[0].name == "products/form.html"
    assert response.context["form"].instance == product
    assert "Редактировать средство" in html
    assert "Тушь для ресниц" in html
    assert 'value="2027-03-15"' in html


def test_product_update_changes_existing_product() -> None:
    product = Product.objects.create(
        name="Тестовая пудра",
        brand=Brand.objects.get(name="Maybelline"),
        category=Category.objects.get(name="Лицо"),
        quantity=1,
        expiry_date=localdate() + timedelta(days=90),
    )
    products_before = Product.objects.count()
    response = make_client().post(
        reverse("products:update", args=[product.slug]),
        {
            "name": "Обновлённая пудра",
            "brand": product.brand_id,
            "category": product.category_id,
            "quantity": 4,
            "expiry_date": localdate() + timedelta(days=180),
        },
    )

    try:
        product.refresh_from_db()
        assert response.status_code == 302
        assert response.url == product.get_absolute_url()
        assert Product.objects.count() == products_before
        assert product.name == "Обновлённая пудра"
        assert product.quantity == 4
    finally:
        product.delete()


def test_product_update_does_not_save_invalid_changes() -> None:
    product = Product.objects.create(
        name="Тестовая сыворотка",
        brand=Brand.objects.get(name="L'Oreal"),
        category=Category.objects.get(name="Лицо"),
        quantity=2,
        expiry_date=localdate() + timedelta(days=90),
    )
    response = make_client().post(
        reverse("products:update", args=[product.slug]),
        {
            "name": "Испорченная сыворотка",
            "brand": product.brand_id,
            "category": product.category_id,
            "quantity": 2,
            "expiry_date": localdate() - timedelta(days=1),
        },
    )

    try:
        product.refresh_from_db()
        assert response.status_code == 200
        assert product.name == "Тестовая сыворотка"
        assert "Срок годности не может быть в прошлом" in (
            response.content.decode()
        )
    finally:
        product.delete()


def test_product_delete_get_only_displays_confirmation() -> None:
    product = Product.objects.get(name="Шампунь")
    response = make_client().get(
        reverse("products:delete", args=[product.slug])
    )
    html = response.content.decode()

    assert response.status_code == 200
    assert response.templates[0].name == "products/confirm_delete.html"
    assert Product.objects.filter(pk=product.pk).exists()
    assert "Удалить средство" in html
    assert 'name="csrfmiddlewaretoken"' in html


def test_product_delete_post_removes_product() -> None:
    product = Product.objects.create(
        name="Средство для удаления",
        brand=Brand.objects.get(name="Estel"),
        category=Category.objects.get(name="Волосы"),
        quantity=0,
        expiry_date=localdate() + timedelta(days=30),
    )
    product_id = product.pk
    response = make_client().post(
        reverse("products:delete", args=[product.slug])
    )

    assert response.status_code == 302
    assert response.url == reverse("products:list")
    assert not Product.objects.filter(pk=product_id).exists()


def test_product_delete_rejects_post_without_csrf_token() -> None:
    product = Product.objects.create(
        name="Защищённое средство",
        brand=Brand.objects.get(name="Estel"),
        category=Category.objects.get(name="Волосы"),
        quantity=1,
        expiry_date=localdate() + timedelta(days=30),
    )
    response = Client(
        HTTP_HOST="localhost",
        enforce_csrf_checks=True,
    ).post(reverse("products:delete", args=[product.slug]))

    try:
        assert response.status_code == 403
        assert Product.objects.filter(pk=product.pk).exists()
    finally:
        product.delete()


def test_unknown_product_update_and_delete_return_404() -> None:
    for route_name in ("products:update", "products:delete"):
        response = make_client().get(
            reverse(route_name, args=["unknown-product"])
        )

        assert response.status_code == 404


def test_base_template_loads_shared_navigation() -> None:
    html = render_to_string(
        "base.html",
        {
            "site_name": "Cosmetic Inventory System",
            "inventory_products_count": 3,
        },
    )

    assert "<title>Cosmetic Inventory System</title>" in html
    assert 'href="/"' in html
    assert 'href="/products/"' in html
    assert 'href="/products/attention/"' in html
    assert 'href="/products/statistics/"' in html
    assert "Средства (3)" in html
    assert "Перейти к содержимому" in html
    assert '<main id="main-content"' in html
    assert 'href="/static/css/style.css"' in html
    assert 'src="/static/js/main.js"' in html
    assert 'src="/static/img/logo.svg"' in html
    assert "data-current-year" in html


def test_inventory_context_is_available_on_main_pages() -> None:
    for path in ("/", "/products/", "/products/statistics/"):
        response = make_client().get(path)
        html = response.content.decode()

        assert response.context["site_name"] == (
            "Cosmetic Inventory System"
        )
        assert response.context["inventory_products_count"] == 3
        assert "Средства (3)" in html


def test_main_pages_keep_database_queries_bounded() -> None:
    expected_queries = {
        "/": 1,
        "/products/": 4,
        "/products/attention/": 2,
    }

    for path, expected_count in expected_queries.items():
        with CaptureQueriesContext(connection) as queries:
            response = make_client().get(path)

        assert response.status_code == 200
        assert len(queries) == expected_count


def test_static_assets_are_discoverable() -> None:
    assert finders.find("css/style.css") is not None
    assert finders.find("js/main.js") is not None
    assert finders.find("img/logo.svg") is not None


def test_homepage() -> None:
    response = make_client().get("/")
    html = response.content.decode()

    assert response.status_code == 200
    assert response.templates[0].name == "homepage/index.html"
    assert response.context["page_title"] == "Cosmetic Inventory System"
    assert "Cosmetic Inventory System" in html
    assert "bootstrap@5.3.3" in html
    assert 'href="/products/"' in html
    assert 'aria-current="page"' in html


def test_products_list_uses_orm_data() -> None:
    with patch("products.views.current_date", return_value=FIXED_TODAY):
        response = make_client().get("/products/")

    html = response.content.decode()

    assert response.status_code == 200
    assert response.templates[0].name == "products/list.html"
    assert "products/includes/product_card.html" in {
        template.name for template in response.templates
    }
    assert len(response.context["product_items"]) == 3
    assert response.context["page_obj"].paginator.count == 3
    assert response.context["filter_form"].is_bound is False
    assert "Тональный крем" in html
    assert "Тушь для ресниц" in html
    assert "Шампунь" in html
    assert "Всего позиций: 3" in html
    assert "Требует внимания" in html
    assert "В порядке" in html
    assert 'href="/products/tonalnyi-krem-1/"' in html
    assert 'href="/products/tush-dlia-resnits-2/"' in html
    assert 'href="/products/shampun-3/"' in html


def test_products_list_handles_empty_result() -> None:
    response = make_client().get(
        "/products/",
        {"q": "несуществующее средство"},
    )

    html = response.content.decode()
    assert response.status_code == 200
    assert "Всего позиций: 0" in html
    assert "Список средств пуст" in html
    assert "По заданным условиям средства не найдены" in html


def test_products_search_uses_query_parameter() -> None:
    response = make_client().get("/products/", {"q": "Maybelline"})
    html = response.content.decode()

    assert response.status_code == 200
    assert len(response.context["product_items"]) == 1
    assert response.context["query"] == "Maybelline"
    assert "Тушь для ресниц" in html
    assert "Тональный крем" not in html
    assert "Сбросить фильтры" in html


def test_products_filter_uses_selected_category() -> None:
    response = make_client().get("/products/", {"category": "Лицо"})
    html = response.content.decode()

    assert response.status_code == 200
    assert len(response.context["product_items"]) == 1
    assert response.context["selected_category"] == "Лицо"
    assert "Тональный крем" in html
    assert "Тушь для ресниц" not in html
    assert "selected" in html


def test_products_search_and_category_filter_work_together() -> None:
    response = make_client().get(
        "/products/",
        {"q": "Т", "category": "Глаза"},
    )
    html = response.content.decode()

    assert response.status_code == 200
    assert len(response.context["product_items"]) == 1
    assert "Тушь для ресниц" in html
    assert "Тональный крем" not in html


def test_products_sort_by_quantity() -> None:
    response = make_client().get(
        "/products/",
        {"sort": "quantity"},
    )

    names = [
        item["product"].name
        for item in response.context["product_items"]
    ]
    assert names == [
        "Шампунь",
        "Тональный крем",
        "Тушь для ресниц",
    ]
    assert response.context["selected_sort"] == "quantity"


def test_products_handle_invalid_sort_and_page_parameters() -> None:
    response = make_client().get(
        "/products/",
        {
            "sort": "unknown",
            "page": "not-a-number",
        },
    )

    assert response.status_code == 200
    assert response.context["selected_sort"] == "expiry"
    assert response.context["page_obj"].number == 1
    assert "sort" in response.context["filter_form"].errors
    assert "Исправьте параметры фильтрации" in response.content.decode()


def test_products_paginate_and_preserve_query_parameters() -> None:
    brand = Brand.objects.get(name="L'Oreal")
    category = Category.objects.get(name="Лицо")
    added_products = [
        Product.objects.create(
            name=f"Тестовое средство {number}",
            brand=brand,
            category=category,
            quantity=number,
            expiry_date=date(2028, 1, number + 1),
        )
        for number in range(7)
    ]

    try:
        response = make_client().get(
            "/products/",
            {
                "category": "Лицо",
                "sort": "name",
                "page": "2",
            },
        )
        html = response.content.decode()

        page_obj = response.context["page_obj"]
        assert page_obj.paginator.count == 8
        assert page_obj.paginator.num_pages == 2
        assert page_obj.number == 2
        assert len(response.context["product_items"]) == 2
        assert "page=1" in html
        assert "sort=name" in html
        assert "category=%D0%9B%D0%B8%D1%86%D0%BE" in html
    finally:
        Product.objects.filter(
            pk__in=[product.pk for product in added_products]
        ).delete()


def test_product_detail_uses_orm_data() -> None:
    with patch("products.views.current_date", return_value=FIXED_TODAY):
        response = make_client().get("/products/tonalnyi-krem-1/")

    html = response.content.decode()

    assert response.status_code == 200
    assert response.templates[0].name == "products/detail.html"
    assert response.context["product"].id == 1
    assert response.context["needs_attention"] is True
    assert "Тональный крем" in html
    assert "L&#x27;Oreal" in html
    assert "Лицо" in html
    assert "1 шт." in html
    assert "Заканчивается, стоит добавить в список покупок" in html
    assert "01.12.2026" in html
    assert 'href="/products/"' in html
    assert 'href="/products/tonalnyi-krem-1/edit/"' in html
    assert 'href="/products/tonalnyi-krem-1/delete/"' in html


def test_product_detail_displays_normal_status() -> None:
    with patch("products.views.current_date", return_value=FIXED_TODAY):
        response = make_client().get("/products/tush-dlia-resnits-2/")

    html = response.content.decode()
    assert response.status_code == 200
    assert response.context["needs_attention"] is False
    assert response.context["quantity_status"] == "В наличии"
    assert "В порядке" in html
    assert "15.03.2027" in html


def test_product_detail_displays_uploaded_image() -> None:
    with tempfile.TemporaryDirectory() as media_root:
        with override_settings(MEDIA_ROOT=media_root):
            product = Product.objects.create(
                name="Изображаемый крем",
                brand=Brand.objects.get(name="Maybelline"),
                category=Category.objects.get(name="Лицо"),
                quantity=2,
                expiry_date=localdate() + timedelta(days=90),
                image=make_product_image(),
            )

            try:
                response = make_client().get(product.get_absolute_url())
                html = response.content.decode()

                assert response.status_code == 200
                assert product.image.url in html
                assert 'alt="Изображаемый крем"' in html
            finally:
                product.delete()


def test_templates_escape_product_data() -> None:
    brand = Brand.objects.create(name="<b>Brand</b>")
    category = Category.objects.create(name="<i>Category</i>")
    product = Product.objects.create(
        name="<script>alert('test')</script>",
        brand=brand,
        category=category,
        quantity=2,
        expiry_date=date(2027, 12, 1),
    )

    try:
        with patch(
            "products.views.current_date",
            return_value=FIXED_TODAY,
        ):
            response = make_client().get(
                "/products/",
                {"q": "alert"},
            )
    finally:
        product.delete()
        brand.delete()
        category.delete()

    html = response.content.decode()
    assert "&lt;script&gt;alert(&#x27;test&#x27;)&lt;/script&gt;" in html
    assert "&lt;b&gt;Brand&lt;/b&gt;" in html
    assert "&lt;i&gt;Category&lt;/i&gt;" in html
    assert "<script>alert('test')</script>" not in html


def test_attention_page_uses_orm_stock_and_expiry_filters() -> None:
    with patch("products.views.current_date", return_value=FIXED_TODAY):
        response = make_client().get("/products/attention/")
    html = response.content.decode()

    assert response.status_code == 200
    assert response.templates[0].name == "products/attention.html"
    assert len(response.context["product_items"]) == 2
    assert "Тональный крем" in html
    assert "Шампунь" in html
    assert "Тушь для ресниц" not in html
    assert "01.12.2026" in html
    assert 'aria-current="page"' in html


def test_statistics_page_uses_orm_aggregates() -> None:
    with patch("products.views.current_date", return_value=FIXED_TODAY):
        response = make_client().get("/products/statistics/")
    html = response.content.decode()

    assert response.status_code == 200
    assert response.templates[0].name == "products/statistics.html"
    assert response.context["totals"]["products_count"] == 3
    assert response.context["totals"]["total_quantity"] == 3
    assert response.context["totals"]["brands_count"] == 3
    assert response.context["totals"]["categories_count"] == 3
    assert response.context["attention_count"] == 2
    assert "По категориям" in html
    assert "По брендам" in html
    assert "L&#x27;Oreal" in html
    assert "Maybelline" in html
    assert "средствами Django ORM" in html


def test_unknown_product_returns_404() -> None:
    response = make_client().get("/products/unknown-product/")
    html = response.content.decode()

    assert response.status_code == 404
    assert response.templates[0].name == "products/not_found.html"
    assert response.context["product_slug"] == "unknown-product"
    assert "Средство не найдено" in html
    assert "unknown-product" in html
    assert "К списку средств" in html


@override_settings(DEBUG=False)
def test_unknown_route_uses_custom_404_page() -> None:
    response = make_client().get("/nonexistent/")
    html = response.content.decode()

    assert response.status_code == 404
    assert response.templates[0].name == "404.html"
    assert "404: страница не найдена" in html
    assert "Страница не найдена" in html
    assert "На главную" in html
    assert "bootstrap@5.3.3" in html


def test_views_delegate_html_to_templates() -> None:
    from homepage import views as homepage_views
    from products import views as product_views

    homepage_source = inspect.getsource(homepage_views)
    products_source = inspect.getsource(product_views)

    assert "def page(" not in homepage_source
    for source in (homepage_source, products_source):
        assert "<html" not in source
        assert "<section" not in source
        assert "HttpResponse(" not in source

    assert "db.queries" not in products_source
    assert "sqlite3" not in products_source
    assert "cursor.execute" not in products_source
