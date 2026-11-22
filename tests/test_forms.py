from datetime import timedelta

from django.utils.timezone import localdate

from products.forms import ProductFilterForm, ProductForm
from products.models import Brand, Category


def test_product_filter_form_cleans_valid_get_parameters() -> None:
    category = Category.objects.get(name="Лицо")
    form = ProductFilterForm(
        {
            "q": "  Maybelline  ",
            "category": category.name,
            "sort": "quantity",
        }
    )

    assert form.is_valid()
    assert form.cleaned_data == {
        "q": "Maybelline",
        "category": category,
        "sort": "quantity",
    }


def test_product_filter_form_rejects_unknown_choices() -> None:
    form = ProductFilterForm(
        {
            "category": "Несуществующая категория",
            "sort": "unknown",
        }
    )

    assert not form.is_valid()
    assert set(form.errors) == {"category", "sort"}


def test_product_filter_form_configures_labels_and_widgets() -> None:
    form = ProductFilterForm()

    assert form.fields["q"].label == "Поиск"
    assert form.fields["q"].widget.input_type == "search"
    assert form.fields["q"].widget.attrs["class"] == "form-control"
    assert form.fields["category"].label == "Категория"
    assert form.fields["category"].widget.attrs["class"] == "form-select"
    assert form.fields["sort"].label == "Сортировка"
    assert form.fields["sort"].initial == "expiry"


def test_product_form_saves_allowed_fields() -> None:
    brand = Brand.objects.get(name="Maybelline")
    category = Category.objects.get(name="Глаза")
    form = ProductForm(
        {
            "name": "  Подводка для глаз  ",
            "brand": brand.pk,
            "category": category.pk,
            "quantity": 2,
            "expiry_date": localdate() + timedelta(days=90),
        }
    )

    assert form.is_valid(), form.errors
    product = form.save()

    try:
        assert product.name == "Подводка для глаз"
        assert product.brand == brand
        assert product.category == category
        assert product.quantity == 2
        assert product.slug.endswith(f"-{product.pk}")
    finally:
        product.delete()


def test_product_form_rejects_expired_product() -> None:
    brand = Brand.objects.get(name="Estel")
    category = Category.objects.get(name="Волосы")
    form = ProductForm(
        {
            "name": "Просроченная маска",
            "brand": brand.pk,
            "category": category.pk,
            "quantity": 1,
            "expiry_date": localdate() - timedelta(days=1),
        }
    )

    assert not form.is_valid()
    assert form.errors["expiry_date"] == [
        "Срок годности не может быть в прошлом."
    ]


def test_product_form_exposes_only_editable_inventory_fields() -> None:
    form = ProductForm()

    assert tuple(form.fields) == (
        "name",
        "brand",
        "category",
        "quantity",
        "expiry_date",
    )
    assert form.fields["name"].widget.attrs["class"] == "form-control"
    assert form.fields["brand"].widget.attrs["class"] == "form-select"
    assert form.fields["expiry_date"].widget.input_type == "date"
