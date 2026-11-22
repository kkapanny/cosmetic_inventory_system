from django import forms

from products.models import Category


PRODUCT_SORT_CHOICES = (
    ("expiry", "По сроку годности"),
    ("name", "По названию"),
    ("quantity", "По количеству"),
)


class ProductFilterForm(forms.Form):
    q = forms.CharField(
        label="Поиск",
        required=False,
        widget=forms.SearchInput(
            attrs={
                "class": "form-control",
                "placeholder": "Название, бренд или категория",
            }
        ),
    )
    category = forms.ModelChoiceField(
        label="Категория",
        required=False,
        queryset=Category.objects.all(),
        to_field_name="name",
        empty_label="Все категории",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    sort = forms.ChoiceField(
        label="Сортировка",
        required=False,
        choices=PRODUCT_SORT_CHOICES,
        initial="expiry",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def clean_sort(self) -> str:
        return self.cleaned_data["sort"] or "expiry"
