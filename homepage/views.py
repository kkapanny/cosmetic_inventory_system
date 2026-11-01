from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def index(request: HttpRequest) -> HttpResponse:
    context = {
        "page_title": "Cosmetic Inventory System",
    }
    return render(request, "homepage/index.html", context)


def page_not_found(
    request: HttpRequest, exception: Exception
) -> HttpResponse:
    context = {
        "page_title": "404: страница не найдена",
    }
    return render(
        request,
        "404.html",
        context,
        status=404,
    )
