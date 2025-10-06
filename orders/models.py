from django.db import models
from django.conf import settings
from products.models import Product

class Order(models.Model):
    STATUS_CHOICES = [
        ('оформлен', 'Оформлен'),
        ('в_работе', 'В работе'),
        ('отправлен', 'Отправлен'),
    ]
    
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='orders',
        verbose_name="Покупатель"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='оформлен',
        verbose_name="Статус"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Заказ #{self.id} - {self.customer.email}"

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE,
        verbose_name="Товар"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    price_at_moment = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Цена на момент заказа"
    )
    
    class Meta:
        verbose_name = "Элемент заказа"
        verbose_name_plural = "Элементы заказа"
    
    def __str__(self):
        return f"{self.product.title} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        # Фиксируем цену товара на момент заказа
        if not self.price_at_moment:
            self.price_at_moment = self.product.price
        super().save(*args, **kwargs)