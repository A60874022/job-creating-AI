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
            item_titles = ", ".join([item.product.title for item in master_items[:3]])
            
            if master_items.count() > 3:
                item_titles += f" и ещё {master_items.count() - 3} товаров"
            
            total_for_master = sum(item.total_price for item in master_items)
            
            from orders.models import Order
            order_content_type = ContentType.objects.get_for_model(Order)
            
            Notification.objects.create(
                user=master,
                notification_type='new_order',
                title='🎉 Новый заказ!',
                message=f'Покупатель {order.customer.email} оформил заказ на ваши товары: {item_titles}. Общая сумма: {total_for_master} ₽.',
                action_url=f'/orders/sales/',
                related_object_id=order.id,
                related_content_type=order_content_type
            )
            return True
        except Exception as e:
            print(f"Error creating notification: {e}")
            return False
    
    @staticmethod
    def create_message_notification(sender, recipient, message_text, dialogue_id):
        """Создание уведомления о новом сообщении"""
        try:
            from chat.models import Dialogue
            dialogue_content_type = ContentType.objects.get_for_model(Dialogue)
            
            # Проверяем, есть ли уже уведомление о непрочитанных сообщениях в этом диалоге
            existing_notification = Notification.objects.filter(
                user=recipient,
                notification_type='new_message',
                related_object_id=dialogue_id,
                related_content_type='dialogue',
                is_read=False
            ).first()
            
            if existing_notification:
                # Обновляем существующее уведомление
                existing_notification.message = f'Новое сообщение от {sender.email}: {message_text[:100]}{"..." if len(message_text) > 100 else ""}'
                existing_notification.save()
            else:
                # Создаем новое уведомление
                Notification.objects.create(
                    user=recipient,
                    notification_type='new_message',
                    title='💬 Новое сообщение',
                    message=f'{sender.email}: {message_text[:100]}{"..." if len(message_text) > 100 else ""}',
                    action_url=f'/chat/dialogue/{dialogue_id}/',
                    related_object_id=dialogue_id,
                    related_content_type='dialogue'
                )
            return True
        except Exception as e:
            print(f"Error creating message notification: {e}")
            return False
    
    @staticmethod
    def mark_dialogue_notifications_read(user, dialogue_id):
        """Пометить все уведомления о сообщениях в диалоге как прочитанные"""
        Notification.objects.filter(
            user=user,
            notification_type='new_message',
            related_object_id=dialogue_id,
            related_content_type='dialogue',
            is_read=False
        ).update(is_read=True)
    
    @staticmethod
    def delete_dialogue_notifications(user, dialogue_id):
        """Удалить все уведомления о сообщениях в диалоге"""
        Notification.objects.filter(
            user=user,
            notification_type='new_message',
            related_object_id=dialogue_id,
            related_content_type='dialogue'
        ).delete()
    
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
                action_url=f'/orders/sales/',
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
                action_url=f'/orders/purchases/',
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
    
    @staticmethod
    def delete_read_notifications(user):
        """Удалить все прочитанные уведомления"""
        deleted_count, _ = Notification.objects.filter(user=user, is_read=True).delete()
        return deleted_count
    
    @staticmethod
    def delete_single_notification(user, notification_id):
        """Удалить одно уведомление (только прочитанное)"""
        try:
            notification = Notification.objects.get(id=notification_id, user=user)
            if notification.is_read:
                notification.delete()
                return True
            return False
        except Notification.DoesNotExist:
            return False