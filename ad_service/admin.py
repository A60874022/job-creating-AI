# chat/admin.py
from django.contrib import admin
from .models import Dialogue, Message

@admin.register(Dialogue)
class DialogueAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'master', 'product', 'created_at']
    list_filter = ['created_at']
    search_fields = ['customer__email', 'master__email']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'dialogue', 'sender', 'created_at', 'is_read']
    list_filter = ['created_at', 'is_read']
    search_fields = ['text', 'sender__email']