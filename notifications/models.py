from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('new_order', '🎉 Новый заказ'),
        ('order_status_changed', '📦 Статус заказа изменен'),
        ('new_message', '💬 Новое сообщение'),
        ('product_favorited', '❤️ Товар добавлен в избранное'),
        ('system', '🔔 Системное уведомление'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    # Ссылки на связанные объекты
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_content_type = models.CharField(max_length=100, blank=True)
    action_url = models.CharField(max_length=500, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} для {self.user.email}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()
    
    @property
    def is_recent(self):
        return (timezone.now() - self.created_at).days < 1