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
                _('Успешная регистрация в качестве мастера! Теперь вы можете добавлять свои товары.')
            )
        else:
            messages.success(
                self.request, 
                _('Успешная регистрация! Начните изучать handmade товары.')
            )
            
        return redirect(self.success_url)
    
    def form_invalid(self, form):
        """Обработка невалидной формы"""
        messages.error(
            self.request, 
            _('Пожалуйста, исправьте ошибки ниже.')
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
        messages.success(self.request, _('Успешный вход в систему!'))
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
    success_url = reverse_lazy('users:password_reset_done')
    
    def form_valid(self, form):
        messages.info(
            self.request,
            _('Если аккаунт с таким email существует, вы получите инструкции по сбросу пароля.')
        )
        return super().form_valid(form)

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Сброс пароля - шаг 3: ввод нового пароля
    """
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')
    
    def form_valid(self, form):
        messages.success(self.request, _('Ваш пароль был успешно сброшен!'))
        return super().form_valid(form)

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """
    Сброс пароля - шаг 4: завершение сброса пароля
    """
    template_name = 'users/password_reset_complete.html'


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserEditForm, ProfileEditForm

@login_required
def edit_profile(request):
    if request.method == 'POST':
        # instance=request.user и instance=request.user.profile заполняют форму текущими данными
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = ProfileEditForm(request.POST, request.FILES, instance=request.user.profile) # request.FILES важен для загрузки изображений!

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Ваш профиль был успешно обновлен!')
            return redirect('users:edit_profile') # Перенаправляем обратно на страницу профиля
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')

    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'users/edit_profile.html', context)