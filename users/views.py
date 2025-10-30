# users/views.py
import logging
from django.views.generic import CreateView, FormView, View
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import render, redirect, get_object_or_404  #

from .models import User
from .forms import UserRegistrationForm, UserLoginForm, EmailVerificationForm, UserEditForm, ProfileEditForm, AccountDeleteForm
from .services.email_service import email_service

logger = logging.getLogger(__name__)


class RegisterView(CreateView):
    """
    Представление для регистрации новых пользователей с подтверждением email через код.
    """
    model = User
    form_class = UserRegistrationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:verify_email_code')

    def form_valid(self, form):
        """
        Обработка валидной формы регистрации.
        """
        try:
            user = form.save(commit=False)
            user.is_active = True
            user.email_verified = False
            user.save()

            # Генерируем и отправляем код подтверждения
            verification_code = user.generate_verification_code()

            email_sent = email_service.send_verification_code_email(
                user_email=user.email,
                verification_code=verification_code,
                context={'user_name': user.get_short_name()}
            )

            # Сохраняем ID пользователя в сессии для подтверждения
            self.request.session['user_id_for_verification'] = user.id
            self.request.session['user_email'] = user.email

            # Логируем
            logger.info(f"User {user.email} registered. Verification code sent: {email_sent}")

            # Сообщение пользователю
            if email_sent:
                messages.success(
                    self.request,
                    _('Код подтверждения отправлен на ваш email. Проверьте почту.')
                )
            else:
                messages.warning(
                    self.request,
                    _('Регистрация завершена, но не удалось отправить код подтверждения. '
                      'Вы можете запросить новый код на странице подтверждения.')
                )

            return redirect(self.success_url)

        except Exception as e:
            logger.error(f"Registration failed for email: {form.cleaned_data.get('email')}. Error: {e}")
            messages.error(
                self.request,
                _('Произошла ошибка при регистрации. Пожалуйста, попробуйте еще раз.')
            )
            return self.form_invalid(form)

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


class EmailVerificationCodeView(FormView):
    """
    Представление для ввода кода подтверждения email
    """
    form_class = EmailVerificationForm
    template_name = 'users/emails/verify_email_code.html'
    success_url = reverse_lazy('home')
    
    def dispatch(self, request, *args, **kwargs):
        """
        Проверяем, что пользователь прошел регистрацию
        """
        if 'user_id_for_verification' not in request.session:
            messages.error(request, _('Сначала завершите регистрацию.'))
            return redirect('users:register')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """
        Добавляем email пользователя в контекст
        """
        context = super().get_context_data(**kwargs)
        context['user_email'] = self.request.session.get('user_email')
        return context
    
    def form_valid(self, form):
        """
        Обработка валидной формы с кодом подтверждения
        """
        user_id = self.request.session.get('user_id_for_verification')
        verification_code = form.cleaned_data['verification_code']
        
        try:
            user = User.objects.get(id=user_id)
            
            if user.verify_email_with_code(verification_code):
                # Успешное подтверждение
                login(self.request, user)
                
                # Очищаем сессию
                self._clear_verification_session()
                
                messages.success(
                    self.request,
                    _('Email успешно подтвержден! Добро пожаловать!')
                )
                logger.info(f"Email verified for user: {user.email}")
                
                return redirect(self.success_url)
            else:
                messages.error(
                    self.request,
                    _('Неверный код подтверждения или срок его действия истек.')
                )
                return self.form_invalid(form)
                
        except User.DoesNotExist:
            messages.error(self.request, _('Пользователь не найден.'))
            return self.form_invalid(form)
    
    def _clear_verification_session(self):
        """
        Очищает данные верификации из сессии
        """
        if 'user_id_for_verification' in self.request.session:
            del self.request.session['user_id_for_verification']
        if 'user_email' in self.request.session:
            del self.request.session['user_email']


class ResendVerificationCodeView(View):
    """
    Представление для повторной отправки кода подтверждения
    """
    
    def post(self, request):
        user_id = request.session.get('user_id_for_verification')
        
        if not user_id:
            messages.error(request, _('Сессия истекла. Пожалуйста, зарегистрируйтесь снова.'))
            return redirect('users:register')
        
        try:
            user = User.objects.get(id=user_id)
            new_code = user.generate_verification_code()
            
            email_sent = email_service.send_verification_code_email(
                user_email=user.email,
                verification_code=new_code,
                context={'user_name': user.get_short_name()}
            )
            
            if email_sent:
                messages.success(
                    request,
                    _('Новый код подтверждения отправлен на ваш email.')
                )
            else:
                messages.error(
                    request,
                    _('Не удалось отправить код подтверждения. Попробуйте позже.')
                )
            
            return redirect('users:verify_email_code')
            
        except User.DoesNotExist:
            messages.error(request, _('Пользователь не найден.'))
            return redirect('users:register')


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
        user = form.get_user()
        if user.email_verified:
            messages.success(self.request, _('Успешный вход в систему!'))
            return super().form_valid(form)
        else:
            # Этот случай должен быть обработан формой, но на всякий случай
            messages.error(self.request, _('Пожалуйста, подтвердите ваш email перед входом.'))
            return self.form_invalid(form)


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


@login_required
def delete_account(request):
    if request.method == 'POST':
        form = AccountDeleteForm(request.POST, user=request.user)
        if form.is_valid():
            # Сохраняем ссылку на пользователя до выхода
            user_to_delete = request.user
            user_email = user_to_delete.email
            
            # Выходим пользователя
            logout(request)
            
            # Удаляем аккаунт (используем сохраненную ссылку)
            user_to_delete.delete()
            
            messages.success(
                request, 
                f'Аккаунт {user_email} был успешно удален. Жаль, что вы уходите!'
            )
            return redirect('home')
    else:
        form = AccountDeleteForm(user=request.user)

    return render(request, 'users/delete_account.html', {'form': form})