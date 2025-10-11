# chat/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


# chat/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Dialogue(models.Model):
    customer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='customer_dialogues'
    )
    master = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='master_dialogues'
    )
    product = models.ForeignKey(
        'products.Product', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='dialogues'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['customer', 'master', 'product']
        ordering = ['-updated_at']

    def __str__(self):
        return f"Диалог {self.customer} - {self.master}"

    @property
    def unread_messages_count(self):
        """Количество непрочитанных сообщений"""
        return self.messages.filter(is_read=False).exclude(
            sender=self.customer if self.customer == self.customer else self.master
        ).count()

class Message(models.Model):
    """Сообщение в диалоге"""
    dialogue = models.ForeignKey(
        Dialogue, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    text = models.TextField(max_length=1000)
    image = models.ImageField(
        upload_to='chat_images/', 
        null=True, 
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']  # Хронологический порядок

    def __str__(self):
        return f"Сообщение от {self.sender}: {self.text[:50]}"