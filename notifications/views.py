from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from .models import Notification
from .services import NotificationService

@login_required
def notification_list(request):
    """Список всех уведомлений"""
    notifications = Notification.objects.filter(user=request.user)
    
    # Помечаем как прочитанные при просмотре полного списка
    if request.GET.get('mark_read'):
        NotificationService.mark_all_as_read(request.user)
    
    context = {
        'notifications': notifications,
        'active_tab': 'notifications'
    }
    return render(request, 'notifications/notification_list.html', context)

@login_required
@require_GET
def unread_count_api(request):
    """API для получения количества непрочитанных уведомлений"""
    count = NotificationService.get_unread_count(request.user)
    return JsonResponse({'count': count})

@login_required
@require_POST
def mark_as_read(request, notification_id):
    """Пометить уведомление как прочитанное"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.mark_as_read()
    return JsonResponse({'success': True})

@login_required
@require_POST
def mark_all_read(request):
    """Пометить все уведомления как прочитанные"""
    NotificationService.mark_all_as_read(request.user)
    return JsonResponse({'success': True})