from datetime import date
from pathlib import Path

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from models.products import find_product_by_id
from storage import load_products


DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "products.json"


def products(request: HttpRequest) -> HttpResponse:
    today = date.today()
    product_items = [
        {
            "product": product,
            "needs_attention": product.needs_restock(today),
        }
        for product in load_products(DATA_FILE)
    ]
    context = {
        "page_title": "Косметические средства",
        "product_items": product_items,
    }
    return render(request, "products/list.html", context)


def product_detail(
    request: HttpRequest, product_id: int
) -> HttpResponse:
    product = find_product_by_id(
        load_products(DATA_FILE),
        product_id,
    )
    if product is None:
        context = {
            "page_title": "Средство не найдено",
            "product_id": product_id,
        }
        return render(
            request,
            "products/not_found.html",
            context,
            status=404,
        )

    today = date.today()
    context = {
        "page_title": product.name,
        "product": product,
        "quantity_status": product.get_quantity_status(),
        "expiry_status": product.get_expiry_status(today),
        "needs_attention": product.needs_restock(today),
    }
    return render(request, "products/detail.html", context)
