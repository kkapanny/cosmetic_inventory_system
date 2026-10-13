from django.http import HttpRequest, HttpResponse


def page(title: str, content: str) -> str:
    bootstrap = (
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3"
        "/dist/css/bootstrap.min.css"
    )
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <link rel="stylesheet" href="{bootstrap}">
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-md bg-white border-bottom">
        <div class="container">
            <a class="navbar-brand" href="/">Cosmetic Inventory</a>
            <div class="navbar-nav">
                <a class="nav-link" href="/">Главная</a>
                <a class="nav-link" href="/products/">Средства</a>
            </div>
        </div>
    </nav>
    <main class="container py-4">{content}</main>
</body>
</html>"""


def index(request: HttpRequest) -> HttpResponse:
    content = """
<section class="py-5 text-center">
    <h1 class="display-4">Cosmetic Inventory System</h1>
    <p class="lead">
        Система учёта косметики, контроля запасов и сроков годности.
    </p>
    <a href="/products/" class="btn btn-primary btn-lg">
        Посмотреть средства
    </a>
</section>
"""
    return HttpResponse(page("Cosmetic Inventory System", content))


def page_not_found(
    request: HttpRequest, exception: Exception
) -> HttpResponse:
    content = """
<section class="py-5 text-center">
    <p class="display-1 fw-bold text-danger mb-2">404</p>
    <h1>Страница не найдена</h1>
    <p class="lead">
        Проверьте адрес или вернитесь на главную страницу.
    </p>
    <a href="/" class="btn btn-primary">
        На главную
    </a>
</section>
"""
    return HttpResponse(
        page("404 — страница не найдена", content),
        status=404,
    )
