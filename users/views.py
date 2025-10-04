from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth import login
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .forms import UserRegistrationForm, UserLoginForm
from .models import User

class RegisterView(CreateView):
    """
    Представление для регистрации новых пользователей.
    Используем CreateView для работы с моделью User.
    """
    model = User
    form_class = UserRegistrationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('home')
    
    def form_valid(self, form):
        """
        Вызывается когда форма валидна.
        Сохраняем пользователя и выполняем автоматический вход.
        """
        # Сохраняем форму, но не коммитим в БД пока
        user = form.save(commit=False)
        
        # Дополнительная обработка если нужно
        user.is_active = True  # активируем пользователя
        
        # Сохраняем пользователя в БД
        user.save()
        
        # Выполняем вход пользователя
        login(self.request, user)
        
        # Добавляем сообщение об успехе
        if user.is_master:
            messages.success(
                self.request, 
                _('Successfully registered as master! You can now add your products.')
            )
        else:
            messages.success(
                self.request, 
                _('Successfully registered! Start exploring handmade products.')
            )
            
        return redirect(self.success_url)
    
    def form_invalid(self, form):
        """Обработка невалидной формы"""
        messages.error(
            self.request, 
            _('Please correct the errors below.')
        )
        return super().form_invalid(form)

from django.contrib.auth.views import LoginView
from django.utils.translation import gettext_lazy as _

class CustomLoginView(LoginView):
    """
    Кастомное представление входа.
    Наследуемся от стандартного LoginView и добавляем наши формы и шаблоны.
    """
    form_class = UserLoginForm
    template_name = 'users/login.html'
    redirect_authenticated_user = True  # перенаправлять если уже авторизован
    
    def form_valid(self, form):
        """Добавляем сообщение об успешном входе"""
        messages.success(self.request, _('Successfully logged in!'))
        return super().form_valid(form)


from django.contrib.auth.views import (
    PasswordResetView, 
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)

class CustomPasswordResetView(PasswordResetView):
    """
    Сброс пароля - шаг 1: ввод email
    """
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')
    
    def form_valid(self, form):
        messages.info(
            self.request,
            _('If an account with that email exists, you will receive password reset instructions.')
        )
        return super().form_valid(form)

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Сброс пароля - шаг 3: ввод нового пароля
    """
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')
    
    def form_valid(self, form):
        messages.success(self.request, _('Your password has been reset successfully!'))
        return super().form_valid(form)