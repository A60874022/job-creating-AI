from django.db import models
from django.conf import settings

class Dialog(models.Model):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='customer_dialogs',
        verbose_name="Покупатель"
    )
    master = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='master_dialogs',
        verbose_name="Мастер"
    )
    product = models.ForeignKey(
        'products.Product', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Товар"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Диалог"
        verbose_name_plural = "Диалоги"
        unique_together = ['customer', 'master', 'product']  # один диалог на пару+товар
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Диалог: {self.customer.email} - {self.master.email}"

class Message(models.Model):
    dialog = models.ForeignKey(
        Dialog, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        verbose_name="Отправитель"
    )
    text = models.TextField(max_length=1000, verbose_name="Текст сообщения")
    image = models.ImageField(
        upload_to='message_images/', 
        null=True, 
        blank=True,
        verbose_name="Изображение"
    )
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время отправки")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    
    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ['timestamp']
    
    def __str__(self):
        return f"Сообщение от {self.sender.email}"

# Create your models here.
