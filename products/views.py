from django.http import HttpRequest, HttpResponse


def products(request: HttpRequest) -> HttpResponse:
    return HttpResponse("Список косметических средств")


def product_detail(
    request: HttpRequest, product_id: int
) -> HttpResponse:
    return HttpResponse(f"Косметическое средство {product_id}")
