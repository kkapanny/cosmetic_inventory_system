from django.http import HttpRequest, HttpResponse

from homepage.views import page


def products(request: HttpRequest) -> HttpResponse:
    content = """
<section class="py-4">
    <h1>Косметические средства</h1>
    <p class="lead">
        Просматривайте косметику, количество и сроки годности.
    </p>
    <div class="alert alert-info" role="alert">
        Список средств будет сформирован из данных проекта.
    </div>
</section>
"""
    return HttpResponse(
        page("Косметические средства", content)
    )


def product_detail(
    request: HttpRequest, product_id: int
) -> HttpResponse:
    content = f"""
<section class="py-4">
    <div class="card shadow-sm">
        <div class="card-body">
            <h1 class="card-title h3">Косметическое средство</h1>
            <p class="card-text">
                Идентификатор:
                <span class="badge text-bg-primary">{product_id}</span>
            </p>
            <a href="/products/" class="btn btn-outline-secondary">
                К списку средств
            </a>
        </div>
    </div>
</section>
"""
    return HttpResponse(
        page(f"Косметическое средство {product_id}", content)
    )
