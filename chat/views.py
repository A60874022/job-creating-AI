# chat/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Dialogue, Message
from products.models import Product
from django.contrib.auth import get_user_model

User = get_user_model()

# chat/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import Dialogue, Message

@login_required
def dialogue_list(request):
    """Список диалогов пользователя"""
    if request.user.is_master:
        dialogues = Dialogue.objects.filter(master=request.user)
    else:
        dialogues = Dialogue.objects.filter(customer=request.user)
    
    return render(request, 'chat/dialogue_list.html', {
        'dialogues': dialogues
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
def dialogue_detail(request, dialogue_id):
    """Страница конкретного диалога"""
    dialogue = get_object_or_404(Dialogue, id=dialogue_id)
    
    # Проверка прав доступа
    if request.user not in [dialogue.customer, dialogue.master]:
        return redirect('chat:dialogue_list')
    
    return render(request, 'chat/dialogue_detail.html', {
        'dialogue': dialogue
    })

@login_required
def start_dialogue_from_product(request, product_id):
    """Начать диалог из карточки товара"""
    product = get_object_or_404(Product, id=product_id)
    
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