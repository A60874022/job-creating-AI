from django.urls import path
from . import views
from .views import customer_profile, add_to_favorites, remove_from_favorites


urlpatterns = [
    path('', views.ProductCatalogView.as_view(), name='catalog'),
    path('add/', views.ProductCreateView.as_view(), name='product_add'),
    path('<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_edit'),
    path('my/', views.ProductListView.as_view(), name='my_products'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),  # Детальная страница
    # ЛК покупателя
    path('customer/profile/', customer_profile, name='customer_profile'),
    path('favorites/add/<int:product_id>/', add_to_favorites, name='add_to_favorites'),
    path('favorites/remove/<int:favorite_id>/', remove_from_favorites, name='remove_from_favorites'),
]