from datetime import date, timedelta

from django.core.paginator import Paginator
from django.db.models import Count, F, Sum
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from products.forms import ProductFilterForm, ProductForm
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
    filter_form = ProductFilterForm(request.GET or None)
    query = ""
    selected_category = ""
    selected_sort = "expiry"
    if filter_form.is_valid():
        query = filter_form.cleaned_data["q"]
        category = filter_form.cleaned_data["category"]
        selected_category = category.name if category else ""
        selected_sort = filter_form.cleaned_data["sort"]
    # сортировка применяется к ORM запросу
    products_query = (
        Product.objects.with_inventory_relations()
        .matching(query)
        .in_category(selected_category)
        .order_by(*PRODUCT_SORTS[selected_sort])
    )
    paginator = Paginator(products_query, PRODUCTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))
    product_items = prepare_product_items(
        page_obj.object_list,
        current_date(),
    )
    context = {
        "page_title": "Косметические средства",
        "product_items": product_items,
        "page_obj": page_obj,
        "filter_form": filter_form,
        "query": query,
        "selected_category": selected_category,
        "selected_sort": selected_sort,
    }
    return render(request, "products/list.html", context)


@require_http_methods(["GET", "POST"])
def product_create(request: HttpRequest) -> HttpResponse:
    form = ProductForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        product = form.save()
        return redirect(product)

    context = {
        "page_title": "Добавить средство",
        "form": form,
        "submit_label": "Сохранить средство",
    }
    return render(request, "products/form.html", context)


def product_detail(
    request: HttpRequest, slug: str
) -> HttpResponse:
    try:
        product = get_object_or_404(
            Product.objects.with_inventory_relations(),
            slug=slug,
        )
    except Http404:
        context = {
            "page_title": "Средство не найдено",
            "product_slug": slug,
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
    products_query = (
        Product.objects.with_inventory_relations()
        .needing_attention(deadline)
        .order_by("expiry_date", "name", "pk")
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
    attention_count = Product.objects.needing_attention(deadline).count()
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
