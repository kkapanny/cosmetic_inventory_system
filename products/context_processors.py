from .models import Product


def inventory_context(request) -> dict[str, object]:
    return {
        "site_name": "Cosmetic Inventory System",
        "inventory_products_count": Product.objects.count(),
    }
