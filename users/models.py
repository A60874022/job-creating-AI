from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
import secrets
from django.core.mail import send_mail

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)




# users/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .utils.token_generator import token_generator  # Импортируем наш генератор токенов


class User(AbstractUser):
    """
    Кастомная модель пользователя с email в качестве идентификатора.
    
    Атрибуты:
        username (None): Отключаем стандартное поле username
        email (EmailField): Уникальный email пользователя с валидацией на уровне БД
        is_master (BooleanField): Флаг, указывающий является ли пользователь мастером
        email_verified (BooleanField): Флаг подтверждения email адреса
        email_verification_token (CharField): Токен для верификации email
        verification_token_created_at (DateTimeField): Время создания токена верификации
    """
    
    username = None
    email = models.EmailField(
        _('email address'), 
        unique=True,
        error_messages={
            'unique': _('Пользователь с таким email уже существует.')
        }
    )
    is_master = models.BooleanField(
        default=False,
        verbose_name=_('мастер'),
        help_text=_('Отметьте, если пользователь является мастером')
    )
    email_verified = models.BooleanField(
        default=False,
        verbose_name=_('email подтвержден'),
        help_text=_('Отметьте, если email адрес был подтвержден')
    )
    email_verification_token = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name=_('токен верификации email'),
        help_text=_('Уникальный токен для подтверждения email адреса')
    )
    verification_token_created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('время создания токена'),
        help_text=_('Время когда был создан токен верификации')
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = _('пользователь')
        verbose_name_plural = _('пользователи')
        db_table = 'auth_user'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['email_verification_token']),
            models.Index(fields=['is_master']),
        ]

    def __str__(self):
        """Строковое представление пользователя - email адрес."""
        return self.email
    
    def clean(self):
        """
        Валидация модели перед сохранением.
        Проверяет корректность email адреса.
        
        Note: Проверка уникальности осуществляется на уровне БД (unique=True)
              и через форму регистрации для лучшего UX.
        """
        super().clean()
        # Базовая валидация email средствами Django
        from django.core.validators import validate_email
        validate_email(self.email)
    
    def generate_verification_token(self) -> str:
        """
        Генерирует и сохраняет токен для верификации email.
        
        Returns:
            str: Сгенерированный токен
        """
        self.email_verification_token = token_generator.generate_verification_token()
        self.verification_token_created_at = timezone.now()
        self.save(update_fields=[
            'email_verification_token', 
            'verification_token_created_at'
        ])
        return self.email_verification_token
    
    def is_verification_token_valid(self) -> bool:
        """
        Проверяет валидность токена верификации.
        
        Returns:
            bool: True если токен действителен, False если истек
        """
        return token_generator.is_token_valid(
            self.verification_token_created_at,
            expiry_hours=48  # Токен действителен 48 часов
        )

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='profile_images', default='default_avatar.jpg', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    city = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f'Профиль {self.user.email}'