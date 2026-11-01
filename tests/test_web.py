import os
from unittest.mock import patch

import django
from django.conf import settings
from django.template.loader import render_to_string
from django.test import Client, override_settings
from django.test.utils import setup_test_environment
from django.urls import reverse


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "cosmetic_inventory.settings",
)
settings.DATABASES["default"]["NAME"] = ":memory:"
django.setup()
setup_test_environment()


# создание тестового HTTP-клиента
def make_client() -> Client:
    return Client(HTTP_HOST="localhost")


def test_named_routes() -> None:
    assert reverse("homepage:index") == "/"
    assert reverse("products:list") == "/products/"
    assert reverse("products:detail", args=[1]) == "/products/1/"


def test_base_template_loads_shared_navigation() -> None:
    html = render_to_string("base.html")

    assert "<title>Cosmetic Inventory System</title>" in html
    assert 'href="/"' in html
    assert 'href="/products/"' in html
    assert "Перейти к содержимому" in html
    assert '<main id="main-content"' in html


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


def test_products_list_uses_json_data() -> None:
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


def test_products_list_handles_empty_storage() -> None:
    with patch("products.views.load_products", return_value=[]):
        response = make_client().get("/products/")

    html = response.content.decode()
    assert response.status_code == 200
    assert "Всего позиций: 0" in html
    assert "Список средств пуст" in html
    assert "После добавления косметических средств" in html


def test_product_detail_uses_json_data() -> None:
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
