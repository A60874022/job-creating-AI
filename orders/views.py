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

@login_required
@transaction.atomic
def create_order(request):
    """Создание заказа из корзины"""
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.select_related('product').all()
    
    if not cart_items:
        messages.error(request, 'Ваша корзина пуста')
        return redirect('orders:cart_view')
    
    # Проверяем, что все товары еще активны
    for item in cart_items:
        if not item.product.is_active:
            messages.error(request, f'Товар "{item.product.title}" больше не доступен')
            return redirect('orders:cart_view')
    
    # Создаем заказ
    order = Order.objects.create(customer=request.user, status='оформлен')
    
    # Создаем элементы заказа
    total_amount = 0
    for cart_item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            quantity=cart_item.quantity,
            price_at_moment=cart_item.product.price
        )
        total_amount += cart_item.product.price * cart_item.quantity
    
    # Обновляем общую сумму заказа
    order.total_amount = total_amount
    order.save()
    
    # Очищаем корзину
    cart.items.all().delete()
    
    messages.success(request, f'Заказ #{order.id} успешно оформлен! Сумма: {total_amount} ₽')
    return redirect('customer_orders')

@login_required
def customer_orders(request):
    """Страница заказов покупателя"""
    orders = Order.objects.filter(customer=request.user).prefetch_related(
        'items__product__images'
    ).order_by('-created_at')
    return render(request, 'orders/customer_orders.html', {'orders': orders})