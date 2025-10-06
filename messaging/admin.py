from django.contrib import admin
from .models import Dialog, Message

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ['sender', 'text', 'image', 'timestamp', 'is_read']
    readonly_fields = ['timestamp']

@admin.register(Dialog)
class DialogAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'master', 'product', 'created_at']
    list_filter = ['created_at']
    search_fields = ['customer__email', 'master__email', 'product__title']
    inlines = [MessageInline]

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'sender', 'dialog', 'timestamp', 'is_read']
    list_filter = ['timestamp', 'is_read']
    search_fields = ['sender__email', 'text']
    readonly_fields = ['timestamp']
