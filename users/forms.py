# users/forms.py
import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _

from .models import Profile, User


def validate_password_no_russian(value):
    """
    Валидатор пароля: проверяет отсутствие русских букв.
    """
    russian_chars_pattern = re.compile("[а-яёА-ЯЁ]")
    if russian_chars_pattern.search(value):
        raise ValidationError(
            _("Пароль не должен содержать русские буквы."),
            code="password_contains_russian",
        )


class UserRegistrationForm(UserCreationForm):
    """
    Кастомная форма регистрации пользователя с расширенной валидацией.
    """

    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": _("your.email@example.com"),
                "autocomplete": "email",
                "autofocus": True,
            }
        ),
        label=_("Email адрес"),
        help_text=_("Введите действующий email адрес."),
        validators=[validate_email],
    )

    class Meta:
        model = User
        fields = ("email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        """
        Инициализация формы с кастомизацией полей.
        """
        super().__init__(*args, **kwargs)

        # Кастомизация поля password1
        self.fields["password1"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": _("Создайте надежный пароль"),
                "autocomplete": "new-password",
            }
        )
        self.fields["password1"].validators.append(validate_password_no_russian)

        # Кастомизация поля password2
        self.fields["password2"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": _("Повторите ваш пароль"),
                "autocomplete": "new-password",
            }
        )

        # Установка лейблов и вспомогательных текстов
        self.fields["password1"].label = _("Пароль")
        self.fields["password2"].label = _("Подтверждение пароля")
        self.fields["password1"].help_text = _(
            "Пароль должен содержать минимум 8 символов, "
            "не состоять только из цифр и не быть слишком простым. "
            "Русские буквы не допускаются."
        )

    def clean_email(self):
        email = self.cleaned_data.get("email").lower().strip()
        try:
            user = User.objects.get(email=email)
            if user.email_verified:
                raise ValidationError(
                    _("Пользователь с таким email уже существует."),
                    code="duplicate_email",
                )
            else:
                # Email есть, но не подтверждён — используем существующего пользователя
                self.instance = user
        except User.DoesNotExist:
            pass
        return email

    def clean_password1(self):
        """
        Валидация пароля.
        """
        password1 = self.cleaned_data.get("password1")

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
        user.email = self.cleaned_data["email"].lower().strip()

        if commit:
            user.save()

        return user


class UserLoginForm(AuthenticationForm):
    """
    Форма входа пользователя.
    Наследуется от AuthenticationForm, меняем username на email.
    """

    username = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": _("your.email@example.com"),
                "autocomplete": "email",
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Password"),
                "autocomplete": "current-password",
            }
        )
    )

    error_messages = {
        "invalid_login": _(
            "Please enter a correct %(username)s and password. "
            "Note that both fields may be case-sensitive."
        ),
        "inactive": _("This account is inactive."),
        "email_not_verified": _("Please verify your email address before logging in."),
    }

    def confirm_login_allowed(self, user):
        """
        Проверяет, может ли пользователь войти в систему.
        """
        if not user.email_verified:
            raise forms.ValidationError(
                self.error_messages["email_not_verified"],
                code="email_not_verified",
            )
        super().confirm_login_allowed(user)


class EmailVerificationForm(forms.Form):
    """
    Форма для ввода кода подтверждения email
    """

    verification_code = forms.CharField(
        label=_("Код подтверждения"),
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Введите 6-значный код"),
                "maxlength": "6",
                "pattern": "[0-9]{6}",
            }
        ),
        help_text=_("Введите 6-значный код, отправленный на ваш email"),
    )

    def clean_verification_code(self):
        """Валидация кода подтверждения"""
        code = self.cleaned_data.get("verification_code", "").strip()
        if not code.isdigit() or len(code) != 6:
            raise ValidationError(
                _("Код должен состоять из 6 цифр."), code="invalid_code_format"
            )
        return code


class UserEditForm(forms.ModelForm):
    # Убираем поле password, чтобы пользователь не видел его в открытом виде
    password = None

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
        )  # Добавляем поля при необходимости


import os

from django import forms
from django.core.validators import MaxLengthValidator, RegexValidator

from .models import Profile


class ProfileEditForm(forms.ModelForm):
    # Переопределяем поле bio для добавления счетчика символов
    bio = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Расскажите о себе и своем творчестве...",
                "class": "form-control",
                "maxlength": "500",
                "data-max-length": "500",
            }
        ),
        label="О себе",
        help_text="Максимум 500 символов",
    )

    # Переопределяем поле city для добавления валидации
    city = forms.CharField(
        max_length=150,
        required=False,
        validators=[
            RegexValidator(
                regex=r"^[а-яА-ЯёЁ\s\-]+$",
                message="Город должен содержать только кириллические буквы, пробелы и дефисы",
            ),
            MaxLengthValidator(
                150, message="Название города не должно превышать 150 символов"
            ),
        ],
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Введите ваш город",
                "pattern": "[а-яА-ЯёЁ\\s\\-]*",
                "title": "Только кириллические буквы, пробелы и дефисы",
            }
        ),
        label="Город",
    )

    # Переопределяем поле avatar для добавления валидации
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(
            attrs={
                "class": "form-control",
                "accept": ".jpg,.jpeg,.png,.gif,.webp",
                "data-max-size": "5242880",  # 5MB в байтах
            }
        ),
        label="Аватар профиля",
    )

    class Meta:
        model = Profile
        fields = ("avatar", "bio", "city")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем CSS классы для валидации
        self.fields["email"] = forms.EmailField(
            required=True,
            widget=forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Введите ваш email"}
            ),
            label="Email адрес",
        )

    def clean_city(self):
        """Кастомная очистка поля city"""
        city = self.cleaned_data.get("city", "").strip()
        if city:
            # Удаляем множественные пробелы
            city = " ".join(city.split())
            # Проверяем, что город не состоит только из пробелов или спецсимволов
            if not any(c.isalpha() for c in city):
                raise forms.ValidationError("Введите корректное название города")
        return city

    def clean_bio(self):
        """Кастомная очистка поля bio"""
        bio = self.cleaned_data.get("bio", "").strip()
        # Можно добавить дополнительную логику очистки если нужно
        return bio

    def clean_avatar(self):
        """Кастомная очистка поля avatar"""
        avatar = self.cleaned_data.get("avatar")

        if avatar:
            # Дополнительная проверка расширения (на всякий случай)
            ext = os.path.splitext(avatar.name)[1].lower()
            if ext == ".tiff" or ext == ".tif":
                raise forms.ValidationError(
                    "Формат TIFF не поддерживается. Используйте JPG, PNG, GIF или WebP."
                )

            # Дополнительная проверка размера
            if avatar.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Размер файла не должен превышать 5MB.")

        return avatar

    def clean(self):
        """Общая валидация формы"""
        cleaned_data = super().clean()

        # Можно добавить кросс-полевые проверки если нужно
        city = cleaned_data.get("city")
        bio = cleaned_data.get("bio")

        # Пример: если указан город, но нет информации о себе - предупреждение
        if city and not bio:
            self.add_warning(
                "bio",
                "Рекомендуем добавить информацию о себе для лучшего представления вашего профиля.",
            )

        return cleaned_data

    def add_warning(self, field, message):
        """Метод для добавления предупреждений (не ошибок)"""
        if not hasattr(self, "_warnings"):
            self._warnings = {}
        self._warnings[field] = message

    def get_warnings(self):
        """Получить предупреждения формы"""
        return getattr(self, "_warnings", {})


class AccountDeleteForm(forms.Form):
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="Я понимаю, что это действие нельзя отменить",
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Введите ваш пароль для подтверждения",
            }
        ),
        label="Текущий пароль",
        required=True,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)  # Извлекаем user из kwargs
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if self.user and not self.user.check_password(password):
            raise forms.ValidationError("Неверный пароль")
        return password
