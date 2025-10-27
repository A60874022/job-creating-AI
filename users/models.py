from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
import secrets
from django.core.mail import send_mail

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import random

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


class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    email_verified = models.BooleanField(_('email verified'), default=False)
    email_verification_code = models.CharField(
        _('email verification code'), 
        max_length=6, 
        blank=True, 
        null=True
    )
    email_verification_code_created_at = models.DateTimeField(
        _('verification code created at'), 
        blank=True, 
        null=True
    )
    is_master = models.BooleanField(_('is master'), default=False)
    
    # Убираем username, используем email
    username = None
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def generate_verification_code(self):
        """Генерирует 6-значный код подтверждения"""
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.email_verification_code = code
        self.email_verification_code_created_at = timezone.now()
        self.save(update_fields=[
            'email_verification_code', 
            'email_verification_code_created_at'
        ])
        return code

    def is_verification_code_valid(self, code):
        """Проверяет валидность кода подтверждения (15 минут)"""
        if (self.email_verification_code == code and 
            self.email_verification_code_created_at):
            expiration_time = self.email_verification_code_created_at + timezone.timedelta(minutes=15)
            return timezone.now() <= expiration_time
        return False

    def verify_email_with_code(self, code):
        """Подтверждает email по коду"""
        if self.is_verification_code_valid(code):
            self.email_verified = True
            self.email_verification_code = None
            self.email_verification_code_created_at = None
            self.save(update_fields=[
                'email_verified',
                'email_verification_code',
                'email_verification_code_created_at'
            ])
            return True
        return False

    def __str__(self):
        return self.email

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='profile_images', default='default_avatar.jpg', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    city = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f'Профиль {self.user.email}'