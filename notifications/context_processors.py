# notifications/context_processors.py
from .models import Notification

def notifications_context(request):
    """Добавляет уведомления в контекст всех шаблонов"""
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).order_by('-created_at')[:5]  # Последние 5 непрочитанных
        
        unread_count = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).count()
        
        return {
            'unread_notifications': unread_notifications,
            'unread_notifications_count': unread_count
        }
    return {}