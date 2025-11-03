# notifications/services.py
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from .models import Notification

class NotificationService:
    
    @staticmethod
    def create_order_notification(order, master):
        """Создание уведомления о новом заказе для мастера"""
        try:
            # Получаем товары этого мастера в заказе
            master_items = order.items.filter(product__master=master)
            item_titles = ", ".join([item.product.title for item in master_items[:3]])  # первые 3 товара
            
            if master_items.count() > 3:
                item_titles += f" и ещё {master_items.count() - 3} товаров"
            
            total_for_master = sum(item.total_price for item in master_items)
            
            # Получаем ContentType для модели Order
            from orders.models import Order
            order_content_type = ContentType.objects.get_for_model(Order)
            
            Notification.objects.create(
                user=master,
                notification_type='new_order',
                title='🎉 Новый заказ!',
                message=f'Покупатель {order.customer.email} оформил заказ на ваши товары: {item_titles}. Общая сумма: {total_for_master} ₽.',
                action_url=f'/orders/master/',
                related_object_id=order.id,
                related_content_type=order_content_type
            )
            return True
        except Exception as e:
            print(f"Error creating notification: {e}")
            return False
    
    @staticmethod
    def create_cancellation_notification(order, master, customer):
        """Создание уведомления об отмене заказа покупателем"""
        try:
            from orders.models import Order
            order_content_type = ContentType.objects.get_for_model(Order)
            
            Notification.objects.create(
                user=master,
                notification_type='order_cancelled',
                title='❌ Заказ отменен',
                message=f'Покупатель {customer.email} отменил заказ #{order.id}',
                action_url=f'/orders/master/',
                related_object_id=order.id,
                related_content_type=order_content_type
            )
            return True
        except Exception as e:
            print(f"Error creating cancellation notification: {e}")
            return False
    
    @staticmethod
    def create_master_cancellation_notification(order, master):
        """Создание уведомления об отмене заказа мастером"""
        try:
            from orders.models import Order
            order_content_type = ContentType.objects.get_for_model(Order)
            
            Notification.objects.create(
                user=order.customer,
                notification_type='order_cancelled',
                title='❌ Заказ отменен мастером',
                message=f'Мастер {master.email} отменил ваш заказ #{order.id}',
                action_url=f'/orders/my/',
                related_object_id=order.id,
                related_content_type=order_content_type
            )
            return True
        except Exception as e:
            print(f"Error creating master cancellation notification: {e}")
            return False
    
    @staticmethod
    def get_unread_count(user):
        """Получение количества непрочитанных уведомлений"""
        return Notification.objects.filter(user=user, is_read=False).count()
    
    @staticmethod
    def mark_all_as_read(user):
        """Пометить все уведомления как прочитанные"""
        Notification.objects.filter(user=user, is_read=False).update(is_read=True)