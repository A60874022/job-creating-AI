from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('api/unread-count/', views.unread_count_api, name='unread_count_api'),
    path('<int:notification_id>/mark-read/', views.mark_as_read, name='mark_as_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
]