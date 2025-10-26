# chat/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Dialogue(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer_dialogues')
    master = models.ForeignKey(User, on_delete=models.CASCADE, related_name='master_dialogues')
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Диалог между {self.customer.email} и {self.master.email}"

class Message(models.Model):
    dialogue = models.ForeignKey(Dialogue, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages') 
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Сообщение от {self.sender.email}: {self.text[:50]}"