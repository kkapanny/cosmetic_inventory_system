from datetime import date

from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from unidecode import unidecode


def build_product_slug(name: str, product_id: int) -> str:
    base_slug = slugify(unidecode(name))[:200].rstrip("-") or "product"
    return f"{base_slug}-{product_id}"


class Brand(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Название",
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = "Бренд"
        verbose_name_plural = "Бренды"


class Category(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Название",
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class Product(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name="Название",
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="Бренд",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="Категория",
    )
    quantity = models.PositiveIntegerField(
        default=0,
        verbose_name="Количество",
    )
    low_stock = models.GeneratedField(
        expression=models.Case(
            models.When(quantity__lte=1, then=models.Value(True)),
            default=models.Value(False),
            output_field=models.BooleanField(),
        ),
        output_field=models.BooleanField(),
        db_persist=True,
        verbose_name="Низкий остаток",
    )
    expiry_date = models.DateField(
        verbose_name="Срок годности",
    )
    slug = models.SlugField(
        max_length=220,
        unique=True,
        editable=False,
        verbose_name="URL-идентификатор",
    )

    @staticmethod
    def validate_quantity(quantity: int) -> bool:
        return quantity >= 0

    def get_expiry_status(self, today: date) -> str:
        days_left = (self.expiry_date - today).days
        if days_left < 0:
            return "Просрочено! Необходимо утилизировать"
        if days_left <= 30:
            return (
                f"Срок годности истекает через {days_left} дн. "
                "Пора заменить"
            )
        return f"Срок годности в порядке (осталось {days_left} дн.)"

    def get_quantity_status(self) -> str:
        if self.quantity == 0:
            return "Средство закончилось"
        if self.quantity == 1:
            return "Заканчивается, стоит добавить в список покупок"
        return "В наличии"

    def needs_restock(self, today: date) -> bool:
        days_left = (self.expiry_date - today).days
        return self.quantity <= 1 or days_left <= 30

    def change_quantity(self, quantity: int) -> None:
        if not self.validate_quantity(quantity):
            raise ValueError("Количество не может быть отрицательным.")
        self.quantity = quantity

    # shortcut: bulk_create требует slug, менеджер нужен при bulk-импорте.
    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            if self.pk:
                self.slug = build_product_slug(self.name, self.pk)
            else:
                super().save(*args, **kwargs)
                self.slug = build_product_slug(self.name, self.pk)
                super().save(update_fields=["slug"])
                return
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse(
            "products:detail",
            kwargs={"slug": self.slug},
        )

    def __str__(self) -> str:
        return f"{self.category} | {self.brand} — {self.name}"

    class Meta:
        ordering = ["expiry_date", "name", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gte=0),
                name="product_quantity_nonnegative",
            ),
        ]
        verbose_name = "Косметическое средство"
        verbose_name_plural = "Косметические средства"
