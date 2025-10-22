from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth import login
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .forms import UserRegistrationForm, UserLoginForm
from .models import User

# users/views.py
import logging
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect, get_object_or_404

from .models import User
from .forms import UserRegistrationForm
from .services.email_service import email_service

logger = logging.getLogger(__name__)


# users/views.py
import logging
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect, get_object_or_404

from .models import User
from .forms import UserRegistrationForm, UserLoginForm  # Импорт в начале файла
from .services.email_service import email_service

logger = logging.getLogger(__name__)


class RegisterView(CreateView):
    """
    Представление для регистрации новых пользователей с подтверждением email.
    """
    
    model = User
    form_class = UserRegistrationForm  # Используем импортированную форму
    template_name = 'users/register.html'
    success_url = reverse_lazy('home')
    
    def form_valid(self, form):
        """
        Обработка валидной формы регистрации.
        """
        try:
            # Сохраняем форму, но не коммитим в БД для дополнительной обработки
            user = form.save(commit=False)
            
            # Устанавливаем флаги пользователя
            user.is_active = True
            user.email_verified = False
            
            # Сохраняем пользователя в БД
            user.save()
            
            # Генерируем и сохраняем токен верификации
            verification_token = user.generate_verification_token()
            
            # Строим URL для подтверждения
            verification_url = self.request.build_absolute_uri(
                f'/users/verify-email/{verification_token}/'
            )
            
            # Отправляем email через сервис
            email_sent = email_service.send_verification_email(
                user_email=user.email,
                verification_url=verification_url,
                context={'user_name': user.get_short_name()}
            )
            
            # Выполняем вход пользователя
            login(self.request, user)
            
            # Логируем успешную регистрацию
            logger.info(f"User {user.email} successfully registered. Email sent: {email_sent}")
            
            # Добавляем соответствующие сообщения об успехе
            self._handle_registration_success(user, email_sent)
            
            return redirect(self.success_url)
            
        except Exception as e:
            logger.error(f"Registration failed for email: {form.cleaned_data.get('email')}. Error: {e}")
            messages.error(
                self.request,
                _('Произошла ошибка при регистрации. Пожалуйста, попробуйте еще раз.')
            )
            return self.form_invalid(form)
    
    def _handle_registration_success(self, user: User, email_sent: bool) -> None:
        """
        Обрабатывает успешную регистрацию пользователя.
        """
        # Базовое сообщение об успехе
        if user.is_master:
            message = _(
                'Успешная регистрация в качестве мастера! '
                'Теперь вы можете добавлять свои товары.'
            )
        else:
            message = _('Успешная регистрация! Начните изучать handmade товары.')
        
        # Добавляем информацию о email
        if email_sent:
            message += ' ' + _('На ваш email отправлено письмо с подтверждением.')
        else:
            message += ' ' + _(
                'Не удалось отправить письмо с подтверждением. '
                'Пожалуйста, обратитесь в поддержку.'
            )
        
        messages.success(self.request, message)
    
    def form_invalid(self, form):
        """
        Обработка невалидной формы регистрации.
        """
        logger.warning(
            f"Registration form validation failed for email: "
            f"{form.cleaned_data.get('email')}. Errors: {form.errors}"
        )
        messages.error(
            self.request, 
            _('Пожалуйста, исправьте ошибки в форме.')
        )
        return super().form_invalid(form)


def verify_email(request, token):
    """
    Представление для подтверждения email адреса по токену.
    """
    try:
        # Ищем пользователя с указанным токеном
        user = get_object_or_404(User, email_verification_token=token)
        
        # Проверяем валидность токена
        if not user.is_verification_token_valid():
            messages.error(
                request, 
                _('Срок действия ссылки подтверждения истек. '
                  'Пожалуйста, запросите новую ссылку.')
            )
            return redirect('home')
        
        # Подтверждаем email и очищаем токен
        user.email_verified = True
        user.email_verification_token = None
        user.save(update_fields=['email_verified', 'email_verification_token'])
        
        # Логируем успешное подтверждение
        logger.info(f"Email verified successfully for user: {user.email}")
        
        # Уведомляем пользователя об успехе
        messages.success(
            request, 
            _('Ваш email адрес успешно подтвержден!')
        )
        
    except User.DoesNotExist:
        # Логируем попытку использования неверного токена
        logger.warning(f"Invalid verification token attempted: {token}")
        
        # Обрабатываем случай неверного токена
        messages.error(
            request, 
            _('Неверная ссылка подтверждения. Пожалуйста, попробуйте еще раз.')
        )
    
    return redirect('home')

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