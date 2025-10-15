# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Profile

class ProfileInline(admin.StackedInline):
    """Inline для отображения профиля пользователя"""
    model = Profile
    can_delete = False
    verbose_name_plural = 'Профиль'
    fields = ['avatar', 'bio', 'city']
    readonly_fields = ['avatar_preview']
    
    def avatar_preview(self, obj):
        if obj.avatar:
            return f'<img src="{obj.avatar.url}" style="max-height: 100px; max-width: 100px;" />'
        return 'Нет аватара'
    avatar_preview.short_description = 'Предпросмотр аватара'
    avatar_preview.allow_tags = True

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админка для пользователей"""
    list_display = ['email', 'first_name', 'last_name', 'is_master', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['is_master', 'is_staff', 'is_superuser', 'is_active', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['email']
    readonly_fields = ['date_joined', 'last_login']
    inlines = [ProfileInline]
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'is_master')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_master', 'is_staff', 'is_active'),
        }),
    )
    
    def get_inline_instances(self, request, obj=None):
        """Показываем inline только при редактировании существующего пользователя"""
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Админка для профилей пользователей"""
    list_display = ['user', 'city', 'bio_preview', 'avatar_preview']
    list_filter = ['city']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'city']
    readonly_fields = ['user', 'avatar_preview']
    list_select_related = ['user']
    
    fieldsets = [
        ('Пользователь', {
            'fields': ['user']
        }),
        ('Информация профиля', {
            'fields': ['avatar', 'avatar_preview', 'bio', 'city']
        }),
    ]
    
    def bio_preview(self, obj):
        """Сокращенное отображение био"""
        if obj.bio:
            return obj.bio[:50] + '...' if len(obj.bio) > 50 else obj.bio
        return '—'
    bio_preview.short_description = 'Био (превью)'
    
    def avatar_preview(self, obj):
        """Предпросмотр аватара"""
        if obj.avatar:
            return f'<img src="{obj.avatar.url}" style="max-height: 100px; max-width: 100px;" />'
        return 'Нет аватара'
    avatar_preview.short_description = 'Предпросмотр аватара'
    avatar_preview.allow_tags = True

    
    def get_readonly_fields(self, request, obj=None):
        """Делаем поле user редактируемым только при создании"""
        if obj:  # редактирование существующего объекта
            return self.readonly_fields + ['user']
        return self.readonly_fields

# Register your models here.
