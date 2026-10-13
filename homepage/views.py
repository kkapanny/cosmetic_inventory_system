from django.http import HttpRequest, HttpResponse


def index(request: HttpRequest) -> HttpResponse:
    return HttpResponse(
        "Cosmetic Inventory System — система учёта косметики"
    )
