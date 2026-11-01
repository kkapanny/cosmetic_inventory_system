from datetime import date, timedelta

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db.queries import (
    get_attention_count,
    get_brand_statistics,
    get_category_statistics,
    get_inventory_totals,
    get_product,
    list_expiring_products,
    list_low_stock_products,
    list_products as fetch_products,
    list_products_by_category,
    search_products,
)
from models import Product


def current_date() -> date:
    return date.today()


def row_to_product(row) -> Product:
    return Product(
        product_id=row["id"],
        name=row["name"],
        brand=row["brand"],
        category=row["category"],
        quantity=row["quantity"],
        expiry_date=date.fromisoformat(row["expiry_date"]),
    )


def prepare_product_items(rows, today: date) -> list[dict[str, object]]:
    product_items = []
    for row in rows:
        product = row_to_product(row)
        product_items.append(
            {
                "product": product,
                "needs_attention": product.needs_restock(today),
            }
        )
    return product_items


def products(request: HttpRequest) -> HttpResponse:
    query = request.GET.get("q", "").strip()
    selected_category = request.GET.get("category", "").strip()

    if query:
        rows = search_products(query, category=selected_category)
    elif selected_category:
        rows = list_products_by_category(selected_category)
    else:
        rows = fetch_products()

    product_items = prepare_product_items(rows, current_date())
    categories = [
        row["category"] for row in get_category_statistics()
    ]
    context = {
        "page_title": "Косметические средства",
        "product_items": product_items,
        "categories": categories,
        "query": query,
        "selected_category": selected_category,
    }
    return render(request, "products/list.html", context)


def product_detail(
    request: HttpRequest, product_id: int
) -> HttpResponse:
    row = get_product(product_id)
    if row is None:
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

    product = row_to_product(row)
    today = current_date()
    context = {
        "page_title": product.name,
        "product": product,
        "quantity_status": product.get_quantity_status(),
        "expiry_status": product.get_expiry_status(today),
        "needs_attention": product.needs_restock(today),
    }
    return render(request, "products/detail.html", context)


def attention(request: HttpRequest) -> HttpResponse:
    today = current_date()
    deadline = today + timedelta(days=30)
    rows = {
        row["id"]: row
        for row in (
            list_low_stock_products()
            + list_expiring_products(deadline)
        )
    }
    ordered_rows = sorted(
        rows.values(),
        key=lambda row: (row["expiry_date"], row["name"]),
    )
    product_items = prepare_product_items(ordered_rows, today)
    context = {
        "page_title": "Требуют внимания",
        "product_items": product_items,
        "deadline": deadline,
    }
    return render(request, "products/attention.html", context)


def statistics(request: HttpRequest) -> HttpResponse:
    deadline = current_date() + timedelta(days=30)
    context = {
        "page_title": "Статистика инвентаря",
        "totals": get_inventory_totals(),
        "attention_count": get_attention_count(deadline),
        "category_statistics": get_category_statistics(),
        "brand_statistics": get_brand_statistics(),
    }
    return render(request, "products/statistics.html", context)
