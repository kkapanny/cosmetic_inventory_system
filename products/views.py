from datetime import date, timedelta

from django.core.paginator import Paginator
from django.db.models import Count, F, Q, Sum
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from products.models import Brand, Category, Product


PRODUCTS_PER_PAGE = 6
PRODUCT_SORTS = {
    "expiry": ("expiry_date", "name", "pk"),
    "name": ("name", "pk"),
    "quantity": ("quantity", "name", "pk"),
}


def current_date() -> date:
    return date.today()


def prepare_product_items(
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
    # сортировка применяется к ORM запросу
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
    product_items = prepare_product_items(
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
    products_query = Product.objects.select_related(
        "brand",
        "category",
    ).filter(
        Q(quantity__lte=1) | Q(expiry_date__lte=deadline)
    ).order_by(
        "expiry_date",
        "name",
        "pk",
    )
    product_items = prepare_product_items(products_query, today)
    context = {
        "page_title": "Требуют внимания",
        "product_items": product_items,
        "deadline": deadline,
    }
    return render(request, "products/attention.html", context)


def statistics(request: HttpRequest) -> HttpResponse:
    deadline = current_date() + timedelta(days=30)
    totals = Product.objects.aggregate(
        products_count=Count("pk"),
        total_quantity=Sum("quantity", default=0),
        brands_count=Count("brand", distinct=True),
        categories_count=Count("category", distinct=True),
    )
    attention_count = Product.objects.filter(
        Q(quantity__lte=1) | Q(expiry_date__lte=deadline)
    ).count()
    category_statistics = (
        Category.objects.annotate(
            products_count=Count("products"),
            total_quantity=Sum("products__quantity", default=0),
        )
        .values(
            "id",
            "products_count",
            "total_quantity",
            category=F("name"),
        )
        .order_by("category")
    )
    brand_statistics = (
        Brand.objects.annotate(
            products_count=Count("products"),
            total_quantity=Sum("products__quantity", default=0),
        )
        .values(
            "id",
            "products_count",
            "total_quantity",
            brand=F("name"),
        )
        .order_by("brand")
    )
    context = {
        "page_title": "Статистика инвентаря",
        "totals": totals,
        "attention_count": attention_count,
        "category_statistics": category_statistics,
        "brand_statistics": brand_statistics,
    }
    return render(request, "products/statistics.html", context)
