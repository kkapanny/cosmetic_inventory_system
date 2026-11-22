from django import forms
from django.core.exceptions import ValidationError
from django.utils.timezone import localdate

from products.models import Category, Product


PRODUCT_SORT_CHOICES = (
    ("expiry", "По сроку годности"),
    ("name", "По названию"),
    ("quantity", "По количеству"),
)
MAX_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


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


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            "name",
            "brand",
            "category",
            "quantity",
            "expiry_date",
            "image",
        )
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Например, увлажняющий крем",
                }
            ),
            "brand": forms.Select(attrs={"class": "form-select"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(
                attrs={"class": "form-control", "min": 0}
            ),
            "expiry_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"class": "form-control", "type": "date"},
            ),
            "image": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/jpeg,image/png,image/webp",
                }
            ),
        }
        help_texts = {
            "quantity": "Укажите количество единиц в наличии.",
            "expiry_date": "Дата должна быть сегодняшней или будущей.",
            "image": "JPEG, PNG или WebP размером не более 5 МБ.",
        }

    def clean_expiry_date(self):
        expiry_date = self.cleaned_data["expiry_date"]
        if expiry_date < localdate():
            raise ValidationError(
                "Срок годности не может быть в прошлом."
            )
        return expiry_date

    def clean_image(self):
        image = self.cleaned_data["image"]
        if not image or not hasattr(image, "content_type"):
            return image
        if image.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
            raise ValidationError(
                "Допустимы изображения JPEG, PNG и WebP."
            )
        if image.size > MAX_IMAGE_SIZE:
            raise ValidationError(
                "Размер изображения не должен превышать 5 МБ."
            )
        return image
