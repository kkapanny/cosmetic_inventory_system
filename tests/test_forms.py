from products.forms import ProductFilterForm
from products.models import Category


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
