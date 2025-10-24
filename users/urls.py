from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from .views import edit_profile

app_name = 'users'

urlpatterns = [
    # Регистрация и вход
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('profile/', edit_profile, name='edit_profile'),
    path('delete-account/', views.delete_account, name='delete_account'),
    # Сброс пароля
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         views.CustomPasswordResetConfirmView.as_view(), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         views.CustomPasswordResetCompleteView.as_view(),  # ← ИЗМЕНИТЕ ЗДЕСЬ
         name='password_reset_complete'),
]