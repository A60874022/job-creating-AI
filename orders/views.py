from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from products.models import Product
from .models import Cart, CartItem, Order, OrderItem

@login_required
def cart_view(request):
    """Просмотр корзины"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('product', 'product__master', 'product__category').all()
    
    print(f"Cart: {cart}")
    print(f"Cart items: {list(cart_items)}")
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    return render(request, 'orders/cart.html', context)

@login_required
def add_to_cart(request, product_id):
    """Добавление товара в корзину"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    # Проверяем, не является ли пользователь мастером этого товара
    if product.master == request.user:
        messages.error(request, 'Вы не можете добавить в корзину свой собственный товар')
        return redirect('product_detail', pk=product_id)
    
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Проверяем, есть ли уже этот товар в корзине
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not item_created:
        # Если товар уже есть в корзине, увеличиваем количество
        cart_item.quantity += 1
        cart_item.save()
        messages.success(request, f'Количество товара "{product.title}" увеличено до {cart_item.quantity}')
    else:
        messages.success(request, f'Товар "{product.title}" добавлен в корзину!')
    
    return redirect('orders:cart_view')

@login_required
def update_cart_item(request, item_id):
    """Обновление количества товара в корзине"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, f'Количество товара обновлено до {quantity}')
        else:
            cart_item.delete()
            messages.success(request, 'Товар удален из корзины')
    
    return redirect('orders:cart_view')

@login_required
def remove_from_cart(request, item_id):
    """Удаление товара из корзины"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_title = cart_item.product.title
    cart_item.delete()
    
    messages.success(request, f'Товар "{product_title}" удален из корзины')
    return redirect('orders:cart_view')

from notifications.services import NotificationService

@login_required
@transaction.atomic
def create_order(request):
    """Создание заказа из корзины"""
    print(f"=== DEBUG: Начало создания заказа для пользователя {request.user.email} ===")
    
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.select_related('product').all()
    
    print(f"DEBUG: Найдено товаров в корзине: {cart_items.count()}")
    
    if not cart_items:
        messages.error(request, 'Ваша корзина пуста')
        return redirect('orders:cart_view')
    
    # Проверяем, что все товары еще активны
    for item in cart_items:
        print(f"DEBUG: Проверка товара: {item.product.title}, тип: {type(item.product)}, ID: {item.product.id}")
        if not item.product.is_active:
            messages.error(request, f'Товар "{item.product.title}" больше не доступен')
            return redirect('orders:cart_view')
    
    try:
        # Создаем заказ
        print("DEBUG: Создаем объект Order...")
        order = Order.objects.create(customer=request.user, status='оформлен')
        print(f"DEBUG: Создан заказ ID: {order.id}")
        
        # Создаем элементы заказа
        total_amount = 0
        masters_notified = set()
        
        for cart_item in cart_items:
            print(f"DEBUG: Обрабатываем CartItem: {cart_item.product.title}")
            print(f"DEBUG: Тип cart_item.product: {type(cart_item.product)}")
            print(f"DEBUG: cart_item.product.__class__: {cart_item.product.__class__}")
            print(f"DEBUG: cart_item.product.id: {cart_item.product.id}")
            
            # Создаем элемент заказа
            print("DEBUG: Создаем OrderItem...")
            order_item = OrderItem.objects.create(
                order=order,
                product=cart_item.product,  # Это должен быть объект Product
                quantity=cart_item.quantity,
                price_at_moment=cart_item.product.price
            )
            print(f"DEBUG: Создан OrderItem ID: {order_item.id}")
            
            total_amount += cart_item.product.price * cart_item.quantity
            
            # Создаем уведомление для мастера
            master = cart_item.product.master
            print(f"DEBUG: Мастер товара: {master.email}, тип: {type(master)}")
            
            if master.id not in masters_notified:
                print(f"DEBUG: Вызываем NotificationService для мастера {master.email}")
                NotificationService.create_order_notification(order, master)
                masters_notified.add(master.id)
        
        # Обновляем общую сумму заказа
        order.total_amount = total_amount
        order.save()
        
        # Очищаем корзину
        cart.items.all().delete()
        
        print(f"DEBUG: Заказ успешно создан! ID: {order.id}, Сумма: {total_amount}")
        messages.success(request, f'Заказ #{order.id} успешно оформлен! Сумма: {total_amount} ₽')
        return redirect('orders:customer_orders')
    
    except Exception as e:
        print(f"=== DEBUG: ОШИБКА ПРИ СОЗДАНИИ ЗАКАЗА ===")
        print(f"Тип ошибки: {type(e)}")
        print(f"Сообщение ошибки: {str(e)}")
        import traceback
        print("Трассировка:")
        traceback.print_exc()
        print("==========================================")
        
        messages.error(request, f'Ошибка при создании заказа: {str(e)}')
        return redirect('orders:cart_view')

@login_required
def customer_orders(request):
    """Страница заказов покупателя"""
    try:
        orders = Order.objects.filter(customer=request.user).prefetch_related(
            'items__product__images',
            'items__product__master'
        ).order_by('-created_at')
    except Exception as e:
        print(f"Error loading orders: {e}")
        orders = []
    
    context = {
        'orders': orders
    }
    return render(request, 'orders/customer_orders.html', context)

# orders/views.py (добавьте эту функцию)
@login_required
def master_orders(request):
    """Страница заказов для мастера"""
    try:
        # Заказы, где есть товары этого мастера
        orders = Order.objects.filter(
            items__product__master=request.user
        ).distinct().prefetch_related(
            'items__product__images',
            'customer'
        ).order_by('-created_at')
    except Exception as e:
        print(f"Error loading master orders: {e}")
        orders = []
    
    context = {
        'orders': orders
    }
    return render(request, 'orders/master_orders.html', context)

@login_required
def delete_order(request, order_id):
    """
    Удаление заказа покупателем
    """
    try:
        # Находим заказ и проверяем, что он принадлежит текущему пользователю
        order = get_object_or_404(Order, id=order_id, customer=request.user)
        
        # Сохраняем ID заказа для сообщения
        order_id = order.id
        
        # Удаляем заказ
        order.delete()
        
        messages.success(request, f'Заказ #{order_id} успешно удален.')
        
    except Exception as e:
        messages.error(request, f'Ошибка при удалении заказа: {str(e)}')
    
    return redirect('orders:customer_orders')

@login_required
def delete_master(request, order_id):
    """
    Представление для удаления заказа мастером
    """
    # Проверяем, что пользователь - мастер
    if not request.user.is_master:
        messages.error(request, "У вас нет прав для выполнения этого действия.")
        return redirect('orders:master_orders')
    
    # Получаем заказ или возвращаем 404 ошибку
    order = get_object_or_404(Order, id=order_id)
    
    # Дополнительная проверка: убеждаемся, что в заказе есть товары этого мастера
    master_items = order.items.filter(product__master=request.user)
    if not master_items.exists():
        messages.error(request, "Этот заказ не содержит ваших товаров.")
        return redirect('orders:master_orders')
    
    try:
        order_id = order.id
        order.delete()
        messages.success(request, f'Заказ #{order_id} был успешно удален.')
    except Exception as e:
        messages.error(request, f'При удалении заказа произошла ошибка: {str(e)}')
    
    return redirect('orders:master_orders')