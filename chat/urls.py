# chat/urls.py
from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.dialogue_list, name='dialogue_list'),
    path('<int:dialogue_id>/', views.dialogue_detail, name='dialogue_detail'),
    path('start/<int:master_id>/', views.start_dialogue, name='start_dialogue'),
    path('start/product/<int:product_id>/', views.start_dialogue_from_product, name='start_dialogue_from_product'),
    path('delete/<int:dialogue_id>/', views.delete_dialogue, name='delete_dialogue'),
    path('clear-all/', views.clear_all_dialogues, name='clear_all_dialogues'),
]