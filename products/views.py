from datetime import date, timedelta

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from db.queries import (
    get_attention_count,
    get_brand_statistics,
    get_category_statistics,
    get_inventory_totals,
    list_expiring_products,
    list_low_stock_products,
)
from models import Product as LegacyProduct
from products.models import Category, Product


PRODUCTS_PER_PAGE = 6
PRODUCT_SORTS = {
    "expiry": ("expiry_date", "name", "pk"),
    "name": ("name", "pk"),
    "quantity": ("quantity", "name", "pk"),
}


def current_date() -> date:
    return date.today()


def row_to_product(row) -> LegacyProduct:
    return LegacyProduct(
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


def prepare_orm_product_items(
    products,
    today: date,
) -> list[dict[str, object]]:
    return [
        {
            "product": product,
            "needs_attention": product.needs_restock(today),
        }
        for product in products
    ]


def products(request: HttpRequest) -> HttpResponse:
    query = request.GET.get("q", "").strip()
    selected_category = request.GET.get("category", "").strip()
    selected_sort = request.GET.get("sort", "expiry")
    if selected_sort not in PRODUCT_SORTS:
        selected_sort = "expiry"

    products_query = Product.objects.select_related(
        "brand",
        "category",
    )
    if query:
        products_query = products_query.filter(
            Q(name__icontains=query)
            | Q(brand__name__icontains=query)
            | Q(category__name__icontains=query)
        )
    if selected_category:
        products_query = products_query.filter(
            category__name=selected_category,
        )

    products_query = products_query.order_by(
        *PRODUCT_SORTS[selected_sort]
    )
    paginator = Paginator(products_query, PRODUCTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))
    product_items = prepare_orm_product_items(
        page_obj.object_list,
        current_date(),
    )
    categories = Category.objects.values_list("name", flat=True)
    context = {
        "page_title": "Косметические средства",
        "product_items": product_items,
        "page_obj": page_obj,
        "categories": categories,
        "query": query,
        "selected_category": selected_category,
        "selected_sort": selected_sort,
    }
    return render(request, "products/list.html", context)


def product_detail(
    request: HttpRequest, product_id: int
) -> HttpResponse:
    try:
        product = get_object_or_404(
            Product.objects.select_related("brand", "category"),
            pk=product_id,
        )
    except Http404:
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
