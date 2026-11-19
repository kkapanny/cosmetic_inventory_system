from django.urls import path

from . import views


app_name = "products"

urlpatterns = [
    path("", views.products, name="list"),
    path("attention/", views.attention, name="attention"),
    path("statistics/", views.statistics, name="statistics"),
    path(
        "<slug:slug>/",
        views.product_detail,
        name="detail",
    ),
]
