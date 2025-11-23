# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Profile, User


class ProfileInline(admin.StackedInline):
    """Inline для отображения профиля пользователя"""

    model = Profile
    can_delete = False
    verbose_name_plural = "Профиль"
    fields = ["avatar", "avatar_preview", "bio", "city"]
    readonly_fields = ["avatar_preview"]

    def avatar_preview(self, obj):
        if obj.avatar and hasattr(obj.avatar, "url"):
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.avatar.url,
            )
        return "Нет аватара"

    avatar_preview.short_description = "Предпросмотр аватара"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админка для пользователей"""

    list_display = [
        "email",
        "first_name",
        "last_name",
        "email_verified",
        "is_staff",
        "is_active",
        "date_joined",
    ]
    list_filter = [
        "email_verified",
        "is_staff",
        "is_superuser",
        "is_active",
        "date_joined",
    ]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["email"]
    readonly_fields = ["date_joined", "last_login", "verification_info"]
    inlines = [ProfileInline]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (
            _("Email verification"),
            {
                "fields": ("email_verified", "verification_info"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            _("Important dates"),
            {"fields": ("last_login", "date_joined"), "classes": ("collapse",)},
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_active"),
            },
        ),
    )

    def verification_info(self, obj):
        if obj.email_verification_code and obj.email_verification_code_created_at:
            return format_html(
                "Код: <strong>{}</strong><br>Создан: {}",
                obj.email_verification_code,
                obj.email_verification_code_created_at,
            )
        return "Нет активного кода верификации"

    verification_info.short_description = "Информация о верификации"

    def get_inline_instances(self, request, obj=None):
        """Показываем inline только при редактировании существующего пользователя"""
        if not obj:
            return []
        return super().get_inline_instances(request, obj)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Админка для профилей пользователей"""

    list_display = ["user", "city", "bio_preview", "avatar_preview"]
    list_filter = ["city"]
    search_fields = ["user__email", "user__first_name", "user__last_name", "city"]
    readonly_fields = ["user", "avatar_preview"]
    list_select_related = ["user"]

    fieldsets = [
        ("Пользователь", {"fields": ["user"]}),
        ("Информация профиля", {"fields": ["avatar", "avatar_preview", "bio", "city"]}),
    ]

    def bio_preview(self, obj):
        """Сокращенное отображение био"""
        if obj.bio:
            return obj.bio[:50] + "..." if len(obj.bio) > 50 else obj.bio
        return "—"

    bio_preview.short_description = "Био (превью)"

    def avatar_preview(self, obj):
        """Предпросмотр аватара"""
        if obj.avatar and hasattr(obj.avatar, "url"):
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.avatar.url,
            )
        return "Нет аватара"

    avatar_preview.short_description = "Предпросмотр аватара"

    def get_readonly_fields(self, request, obj=None):
        """Делаем поле user редактируемым только при создании"""
        if obj:  # редактирование существующего объекта
            return self.readonly_fields + ["user"]
        return self.readonly_fields
