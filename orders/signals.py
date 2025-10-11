from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Cart

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_cart(sender, instance, created, **kwargs):
    """Создаем корзину при создании пользователя"""
    if created:
        Cart.objects.create(user=instance)


# orders/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Order
from notifications.models import Notification

User = get_user_model()

# orders/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Order
from notifications.models import Notification

User = get_user_model()

@receiver(post_save, sender=Order)
def create_new_order_notification(sender, instance, created, **kwargs):
    """
    Создает уведомление для мастера при создании нового заказа
    """
    if created:
        print(f"DEBUG: Сигнал сработал для заказа #{instance.id}")
        
        try:
            # ПРАВИЛЬНЫЙ СПОСОБ: получаем мастеров через элементы заказа
            masters_to_notify = User.objects.filter(
                products__order_items__order=instance  # Используем related_name
            ).distinct()

            print(f"DEBUG: Найдено мастеров для уведомления: {masters_to_notify.count()}")

            for master in masters_to_notify:
                # Получаем товары этого мастера в заказе
                master_items = instance.items.filter(product__master=master)
                item_titles = ", ".join([item.product.title for item in master_items[:3]])

                if master_items.count() > 3:
                    item_titles += f" и ещё {master_items.count() - 3} товаров"

                total_for_master = sum(item.product.price * item.quantity for item in master_items)

                # Создаем уведомление
                Notification.objects.create(
                    user=master,
                    notification_type='new_order',
                    title='🎉 Новый заказ!',
                    message=f'Покупатель {instance.customer.email} оформил заказ на ваши товары: {item_titles}. Общая сумма: {total_for_master} ₽.',
                    action_url=f'/orders/master/orders/',
                    related_object_id=instance.id,
                    related_content_type='order'
                )
                print(f"DEBUG: Создано уведомление для мастера {master.email}")

        except Exception as e:
            print(f"ERROR: Ошибка в сигнале создания уведомления: {e}")
            import traceback
            traceback.print_exc()