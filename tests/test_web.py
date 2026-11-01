import inspect
import os
from datetime import date
from unittest.mock import patch

import django
from django.conf import settings
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.test import Client, override_settings
from django.test.utils import setup_test_environment
from django.urls import reverse

from models import Product


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "cosmetic_inventory.settings",
)
settings.DATABASES["default"]["NAME"] = ":memory:"
django.setup()
setup_test_environment()


FIXED_TODAY = date(2026, 11, 1)


# создание тестового HTTP-клиента
def make_client() -> Client:
    return Client(HTTP_HOST="localhost")


def test_named_routes() -> None:
    assert reverse("homepage:index") == "/"
    assert reverse("products:list") == "/products/"
    assert reverse("products:attention") == "/products/attention/"
    assert reverse("products:statistics") == "/products/statistics/"
    assert reverse("products:detail", args=[1]) == "/products/1/"


def test_base_template_loads_shared_navigation() -> None:
    html = render_to_string("base.html")

    assert "<title>Cosmetic Inventory System</title>" in html
    assert 'href="/"' in html
    assert 'href="/products/"' in html
    assert 'href="/products/attention/"' in html
    assert 'href="/products/statistics/"' in html
    assert "Перейти к содержимому" in html
    assert '<main id="main-content"' in html
    assert 'href="/static/css/style.css"' in html
    assert 'src="/static/js/main.js"' in html
    assert 'src="/static/img/logo.svg"' in html
    assert "data-current-year" in html


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


def test_products_list_uses_sqlite_data() -> None:
    with patch("products.views.current_date", return_value=FIXED_TODAY):
        response = make_client().get("/products/")

    html = response.content.decode()

    assert response.status_code == 200
    assert response.templates[0].name == "products/list.html"
    assert "products/includes/product_card.html" in {
        template.name for template in response.templates
    }
    assert len(response.context["product_items"]) == 3
    assert "Тональный крем" in html
    assert "Тушь для ресниц" in html
    assert "Шампунь" in html
    assert "Всего позиций: 3" in html
    assert "Требует внимания" in html
    assert "В порядке" in html
    assert 'href="/products/1/"' in html
    assert 'href="/products/2/"' in html
    assert 'href="/products/3/"' in html


def test_products_list_handles_empty_result() -> None:
    with patch("products.views.fetch_products", return_value=[]):
        response = make_client().get("/products/")

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


def test_product_detail_uses_sqlite_data() -> None:
    with patch("products.views.current_date", return_value=FIXED_TODAY):
        response = make_client().get("/products/1/")

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


def test_product_detail_displays_normal_status() -> None:
    with patch("products.views.current_date", return_value=FIXED_TODAY):
        response = make_client().get("/products/2/")

    html = response.content.decode()
    assert response.status_code == 200
    assert response.context["needs_attention"] is False
    assert response.context["quantity_status"] == "В наличии"
    assert "В порядке" in html
    assert "15.03.2027" in html


def test_templates_escape_product_data() -> None:
    product = Product(
        product_id=7,
        name="<script>alert('test')</script>",
        brand="<b>Brand</b>",
        category="<i>Category</i>",
        quantity=2,
        expiry_date=date(2027, 12, 1),
    )

    product_row = {
        "id": product.id,
        "name": product.name,
        "brand": product.brand,
        "category": product.category,
        "quantity": product.quantity,
        "expiry_date": product.expiry_date.isoformat(),
    }
    with (
        patch("products.views.fetch_products", return_value=[product_row]),
        patch("products.views.current_date", return_value=FIXED_TODAY),
    ):
        response = make_client().get("/products/")

    html = response.content.decode()
    assert "&lt;script&gt;alert(&#x27;test&#x27;)&lt;/script&gt;" in html
    assert "&lt;b&gt;Brand&lt;/b&gt;" in html
    assert "&lt;i&gt;Category&lt;/i&gt;" in html
    assert "<script>alert('test')</script>" not in html


def test_attention_page_combines_stock_and_expiry_filters() -> None:
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


def test_statistics_page_uses_aggregate_queries() -> None:
    with patch("products.views.current_date", return_value=FIXED_TODAY):
        response = make_client().get("/products/statistics/")
    html = response.content.decode()

    assert response.status_code == 200
    assert response.templates[0].name == "products/statistics.html"
    assert response.context["totals"]["products_count"] == 3
    assert response.context["totals"]["total_quantity"] == 3
    assert response.context["attention_count"] == 2
    assert "По категориям" in html
    assert "По брендам" in html
    assert "L&#x27;Oreal" in html
    assert "Maybelline" in html


def test_unknown_product_returns_404() -> None:
    response = make_client().get("/products/999/")
    html = response.content.decode()

    assert response.status_code == 404
    assert response.templates[0].name == "products/not_found.html"
    assert response.context["product_id"] == 999
    assert "Средство не найдено" in html
    assert "999" in html
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
