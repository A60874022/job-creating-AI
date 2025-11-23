from django.urls import path

from . import views
from .views import (add_to_favorites, profile, remove_from_favorites,
                    remove_from_favorites_by_product)

app_name = "products"

urlpatterns = [
    path("", views.ProductCatalogView.as_view(), name="catalog"),
    path("add/", views.ProductCreateView.as_view(), name="product_add"),
    path("<int:pk>/edit/", views.ProductUpdateView.as_view(), name="product_edit"),
    path("my/", views.ProductListView.as_view(), name="my_products"),
    path("<int:pk>/", views.ProductDetailView.as_view(), name="product_detail"),
    path("<int:pk>/delete/", views.ProductDeleteView.as_view(), name="product_delete"),
    path("autocomplete/", views.product_autocomplete, name="autocomplete"),
    # УНИВЕРСАЛЬНЫЙ ПРОФИЛЬ МАСТЕРА (заменяет customer_profile)
    path("profile/", profile, name="profile"),
    # Избранное
    path("favorites/add/<int:product_id>/", add_to_favorites, name="add_to_favorites"),
    path(
        "favorites/remove/<int:favorite_id>/",
        remove_from_favorites,
        name="remove_from_favorites",
    ),
    path(
        "favorites/remove_by_product/<int:product_id>/",
        remove_from_favorites_by_product,
        name="remove_from_favorites_by_product",
    ),
]
