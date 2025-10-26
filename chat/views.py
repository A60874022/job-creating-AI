from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Count, Q
from .models import Dialogue, Message
from products.models import Product
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def dialogue_list(request):
    """Список диалогов пользователя с аннотацией непрочитанных сообщений"""
    if request.user.is_master:
        dialogues = Dialogue.objects.filter(master=request.user).annotate(
            unread_messages_count=Count(
                'messages',
                filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user)
            )
        ).order_by('-updated_at')
    else:
        dialogues = Dialogue.objects.filter(customer=request.user).annotate(
            unread_messages_count=Count(
                'messages', 
                filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user)
            )
        ).order_by('-updated_at')
    
    return render(request, 'chat/dialogue_list.html', {
        'dialogues': dialogues
    })

@login_required
def dialogue_detail(request, dialogue_id):
    """Страница конкретного диалога"""
    dialogue = get_object_or_404(Dialogue, id=dialogue_id)
    
    # Проверка прав доступа
    if request.user not in [dialogue.customer, dialogue.master]:
        messages.error(request, "У вас нет доступа к этому диалогу")
        return redirect('chat:dialogue_list')
    
    # Определяем собеседника для правильного отображения
    if request.user == dialogue.customer:
        interlocutor = dialogue.master
    else:
        interlocutor = dialogue.customer
    
    # Помечаем сообщения как прочитанные при заходе в диалог
    if request.method == 'GET':
        # Помечаем все непрочитанные сообщения от собеседника как прочитанные
        Message.objects.filter(
            dialogue=dialogue,
            is_read=False
        ).exclude(
            sender=request.user
        ).update(is_read=True)
    
    return render(request, 'chat/dialogue_detail.html', {
        'dialogue': dialogue,
        'interlocutor': interlocutor  # Передаем собеседника в шаблон
    })

@login_required
@require_POST
def mark_messages_read(request, dialogue_id):
    """API endpoint для пометки сообщений как прочитанных"""
    dialogue = get_object_or_404(Dialogue, id=dialogue_id)
    
    # Проверка прав доступа
    if request.user not in [dialogue.customer, dialogue.master]:
        return JsonResponse({'status': 'error', 'message': 'No permission'})
    
    # Помечаем все сообщения собеседника как прочитанные
    messages_to_mark = Message.objects.filter(
        dialogue=dialogue,
        is_read=False
    ).exclude(
        sender=request.user
    )
    
    updated_count = messages_to_mark.update(is_read=True)
    
    return JsonResponse({
        'status': 'success', 
        'updated_count': updated_count
    })

@login_required
def delete_dialogue(request, dialogue_id):
    """Удаление диалога"""
    dialogue = get_object_or_404(Dialogue, id=dialogue_id)
    
    # Проверяем права доступа
    if request.user not in [dialogue.customer, dialogue.master]:
        messages.error(request, "У вас нет прав для удаления этого диалога")
        return redirect('chat:dialogue_list')
    
    if request.method == 'POST':
        # Полное удаление диалога и всех сообщений
        dialogue.messages.all().delete()  # Сначала удаляем сообщения
        dialogue.delete()  # Затем удаляем диалог
        
        messages.success(request, "Диалог успешно удален")
        return redirect('chat:dialogue_list')
    
    return redirect('chat:dialogue_list')

@login_required
def clear_all_dialogues(request):
    """Удаление всех диалогов пользователя"""
    if request.method == 'POST':
        if request.user.is_master:
            dialogues = Dialogue.objects.filter(master=request.user)
        else:
            dialogues = Dialogue.objects.filter(customer=request.user)
        
        deleted_count = dialogues.count()
        
        # Удаляем все сообщения и диалоги
        for dialogue in dialogues:
            dialogue.messages.all().delete()
            dialogue.delete()
        
        messages.success(request, f"Удалено {deleted_count} диалогов")
        return redirect('chat:dialogue_list')
    
    return redirect('chat:dialogue_list')

@login_required
def start_dialogue_from_product(request, product_id):
    """Начать диалог из карточки товара"""
    product = get_object_or_404(Product, id=product_id)
    
    # Проверяем, что пользователь не пытается написать сам себе
    if request.user == product.master:
        messages.error(request, "Вы не можете начать диалог с самим собой")
        return redirect('products:product_detail', product_id=product_id)
    
    # Ищем существующий диалог
    dialogue = Dialogue.objects.filter(
        customer=request.user,
        master=product.master,
        product=product
    ).first()
    
    # Или создаем новый
    if not dialogue:
        dialogue = Dialogue.objects.create(
            customer=request.user,
            master=product.master,
            product=product
        )
    
    return redirect('chat:dialogue_detail', dialogue_id=dialogue.id)

@login_required
def start_dialogue(request, master_id):
    """Начать диалог с мастером"""
    master = get_object_or_404(User, id=master_id, is_master=True)
    
    # Проверяем, что пользователь не пытается написать сам себе
    if request.user == master:
        messages.error(request, "Вы не можете начать диалог с самим собой")
        return redirect('products:catalog')
    
    # Ищем существующий диалог
    dialogue = Dialogue.objects.filter(
        customer=request.user,
        master=master
    ).first()
    
    # Или создаем новый
    if not dialogue:
        dialogue = Dialogue.objects.create(
            customer=request.user,
            master=master
        )
    
    return redirect('chat:dialogue_detail', dialogue_id=dialogue.id)