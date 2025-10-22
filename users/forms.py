from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserChangeForm
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
from .models import User, Profile


import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_password_no_russian(value):
    """
    Валидатор пароля: проверяет отсутствие русских букв.
    
    Args:
        value (str): Пароль для проверки
        
    Raises:
        ValidationError: Если пароль содержит русские буквы
    """
    russian_chars_pattern = re.compile('[а-яёА-ЯЁ]')
    if russian_chars_pattern.search(value):
        raise ValidationError(
            _('Пароль не должен содержать русские буквы.'),
            code='password_contains_russian'
        )


# users/views.py
import logging
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect, get_object_or_404

from .models import User

from .services.email_service import email_service

logger = logging.getLogger(__name__)


# users/forms.py
import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _
from .models import User


def validate_password_no_russian(value):
    """
    Валидатор пароля: проверяет отсутствие русских букв.
    """
    russian_chars_pattern = re.compile('[а-яёА-ЯЁ]')
    if russian_chars_pattern.search(value):
        raise ValidationError(
            _('Пароль не должен содержать русские буквы.'),
            code='password_contains_russian'
        )


class UserRegistrationForm(UserCreationForm):
    """
    Кастомная форма регистрации пользователя с расширенной валидацией.
    """
    
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('your.email@example.com'),
            'autocomplete': 'email',
            'autofocus': True
        }),
        label=_('Email адрес'),
        help_text=_('Введите действующий email адрес.'),
        validators=[validate_email]
    )
    
    is_master = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'role': 'switch'
        }),
        label=_('Я мастер'),
        help_text=_('Отметьте, если хотите продавать свои товары на платформе')
    )

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2', 'is_master')
        
    def __init__(self, *args, **kwargs):
        """
        Инициализация формы с кастомизацией полей.
        """
        super().__init__(*args, **kwargs)
        
        # Кастомизация поля password1
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Создайте надежный пароль'),
            'autocomplete': 'new-password'
        })
        self.fields['password1'].validators.append(validate_password_no_russian)
        
        # Кастомизация поля password2  
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': _('Повторите ваш пароль'),
            'autocomplete': 'new-password'
        })
        
        # Установка лейблов и вспомогательных текстов
        self.fields['password1'].label = _('Пароль')
        self.fields['password2'].label = _('Подтверждение пароля')
        self.fields['password1'].help_text = _(
            'Пароль должен содержать минимум 8 символов, '
            'не состоять только из цифр и не быть слишком простым. '
            'Русские буквы не допускаются.'
        )

    def clean_email(self):
        """
        Валидация email адреса на уникальность.
        """
        email = self.cleaned_data.get('email').lower().strip()
        
        if User.objects.filter(email=email).exists():
            raise ValidationError(
                _('Пользователь с таким email уже существует.'),
                code='duplicate_email'
            )
        return email

    def clean_password1(self):
        """
        Валидация пароля.
        """
        password1 = self.cleaned_data.get('password1')
        
        # Проверка на русские символы
        validate_password_no_russian(password1)
        
        # Стандартная валидация пароля Django
        from django.contrib.auth.password_validation import validate_password
        validate_password(password1)
        
        return password1

    def save(self, commit=True):
        """
        Сохранение пользователя с нормализованным email.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower().strip()
        
        if commit:
            user.save()
            
        return user

from django.contrib.auth.forms import AuthenticationForm

class UserLoginForm(AuthenticationForm):
    """
    Форма входа пользователя.
    Наследуется от AuthenticationForm, меняем username на email.
    """
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('your.email@example.com'),
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Password'),
            'autocomplete': 'current-password'
        })
    )
    
    error_messages = {
        'invalid_login': _(
            "Please enter a correct %(username)s and password. "
            "Note that both fields may be case-sensitive."
        ),
        'inactive': _("This account is inactive."),
    }


class UserEditForm(UserChangeForm):
    # Убираем поле password, чтобы пользователь не видел его в открытом виде
    password = None

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name') # Добавляем поля при необходимости

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('avatar', 'bio', 'city')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Расскажите о себе и своем творчестве...'}),
            'city': forms.TextInput(attrs={'placeholder': 'Ваш город'}),
        }
        labels = {
            'avatar': 'Аватар профиля',
            'bio': 'О себе',
            'city': 'Город',
        }