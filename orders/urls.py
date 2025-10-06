from django.urls import path
from . import views

urlpatterns = [
    path('create/<int:product_id>/', views.create_order, name='create_order'),
    path('my/', views.customer_orders, name='customer_orders'),
]