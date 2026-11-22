from django.urls import path

from . import views


app_name = "products"

urlpatterns = [
    path("", views.products, name="list"),
    path("create/", views.product_create, name="create"),
    path("attention/", views.attention, name="attention"),
    path("statistics/", views.statistics, name="statistics"),
    path("<slug:slug>/edit/", views.product_update, name="update"),
    path("<slug:slug>/delete/", views.product_delete, name="delete"),
    path(
        "<slug:slug>/",
        views.product_detail,
        name="detail",
    ),
]
