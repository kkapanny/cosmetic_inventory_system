import os

import django
from django.conf import settings
from django.test import Client, override_settings


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "cosmetic_inventory.settings",
)
settings.DATABASES["default"]["NAME"] = ":memory:"
django.setup()


# создание тестового HTTP-клиента
def make_client() -> Client:
    return Client(HTTP_HOST="localhost")


def test_homepage() -> None:
    response = make_client().get("/")
    html = response.content.decode()

    assert response.status_code == 200
    assert "Cosmetic Inventory System" in html
    assert "bootstrap@5.3.3" in html
    assert 'href="/products/"' in html


def test_products_list_uses_json_data() -> None:
    response = make_client().get("/products/")
    html = response.content.decode()

    assert response.status_code == 200
    assert "Тональный крем" in html
    assert "Тушь для ресниц" in html
    assert "Шампунь" in html
    assert 'href="/products/1/"' in html
    assert 'href="/products/2/"' in html
    assert 'href="/products/3/"' in html


def test_product_detail_uses_json_data() -> None:
    response = make_client().get("/products/1/")
    html = response.content.decode()

    assert response.status_code == 200
    assert "Тональный крем" in html
    assert "L&#x27;Oreal" in html
    assert "Лицо" in html
    assert "Количество:</strong> 1 шт." in html
    assert "Годен до:</strong>" in html


def test_unknown_product_returns_404() -> None:
    response = make_client().get("/products/999/")
    html = response.content.decode()

    assert response.status_code == 404
    assert "Средство не найдено" in html
    assert "К списку средств" in html


@override_settings(DEBUG=False)
def test_unknown_route_uses_custom_404_page() -> None:
    response = make_client().get("/nonexistent/")
    html = response.content.decode()

    assert response.status_code == 404
    assert "404 — страница не найдена" in html
    assert "На главную" in html
    assert "bootstrap@5.3.3" in html
