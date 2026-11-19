from django.contrib import admin

from .models import Brand, Category, Product


class BrandProductInline(admin.TabularInline):
    model = Product
    fk_name = "brand"
    fields = ("name", "category", "quantity", "expiry_date")
    extra = 0
    show_change_link = True
    verbose_name_plural = "Средства этого бренда"


class CategoryProductInline(admin.TabularInline):
    model = Product
    fk_name = "category"
    fields = ("name", "brand", "quantity", "expiry_date")
    extra = 0
    show_change_link = True
    verbose_name_plural = "Средства этой категории"


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)
    list_per_page = 20
    inlines = (BrandProductInline,)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)
    list_per_page = 20
    inlines = (CategoryProductInline,)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "brand",
        "category",
        "quantity",
        "expiry_date",
        "stock_state",
    )
    list_display_links = ("name",)
    list_editable = ("quantity",)
    search_fields = ("name", "brand__name", "category__name")
    list_filter = ("brand", "category", "expiry_date")
    ordering = ("expiry_date", "name")
    list_per_page = 25
    list_select_related = ("brand", "category")
    readonly_fields = ("stock_state",)
    actions = ("restock_selected",)

    @admin.display(description="Состояние запасов", ordering="quantity")
    def stock_state(self, product: Product) -> str:
        return product.get_quantity_status()

    @admin.action(description="Пополнить выбранные средства до 2 шт.")
    def restock_selected(self, request, queryset) -> None:
        updated = queryset.filter(quantity__lt=2).update(quantity=2)
        self.message_user(
            request,
            f"Пополнено средств: {updated}.",
        )


admin.site.site_header = "Администрирование Cosmetic Inventory System"
admin.site.site_title = "Cosmetic Inventory System"
admin.site.index_title = "Управление косметическим инвентарём"
