from datetime import date
from pathlib import Path

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.html import escape

from homepage.views import page
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
        content = f"""
<section class="py-4">
    <h1 class="text-danger">Средство не найдено</h1>
    <p>Средство с идентификатором {product_id} отсутствует.</p>
    <a href="/products/" class="btn btn-outline-secondary">
        К списку средств
    </a>
</section>
"""
        return HttpResponse(
            page("Средство не найдено", content),
            status=404,
        )

    today = date.today()
    quantity_status = product.get_quantity_status()
    expiry_status = product.get_expiry_status(today)
    attention = product.needs_restock(today)
    attention_text = (
        "Требует пополнения или замены"
        if attention
        else "В порядке"
    )
    attention_badge = (
        "text-bg-warning" if attention else "text-bg-success"
    )

    content = f"""
<section class="py-4">
    <div class="card shadow-sm">
        <div class="card-body">
            <div class="d-flex justify-content-between align-items-start">
                <h1 class="card-title h3">{escape(product.name)}</h1>
                <span class="badge {attention_badge}">
                    {attention_text}
                </span>
            </div>
            <p class="card-text">
                <strong>ID:</strong> {product.id}
            </p>
            <p class="card-text">
                <strong>Бренд:</strong> {escape(product.brand)}
            </p>
            <p class="card-text">
                <strong>Категория:</strong> {escape(product.category)}
            </p>
            <p class="card-text">
                <strong>Количество:</strong> {product.quantity} шт.<br>
                {escape(quantity_status)}
            </p>
            <p class="card-text">
                <strong>Годен до:</strong>
                {product.expiry_date:%d.%m.%Y}<br>
                {escape(expiry_status)}
            </p>
            <a href="/products/" class="btn btn-outline-secondary">
                К списку средств
            </a>
        </div>
    </div>
</section>
"""
    return HttpResponse(
        page(escape(product.name), content),
        status=200,
    )
