from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from products.models import Product
from .models import Order, OrderItem

@login_required
def create_order(request, product_id):
    """Создание заказа для одного товара (упрощенная корзина)"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    # Проверяем, не является ли пользователь мастером этого товара
    if product.master == request.user:
        messages.error(request, 'Вы не можете заказать свой собственный товар')
        return redirect('product_detail', pk=product_id)
    
    # Создаем заказ
    order = Order.objects.create(customer=request.user, status='оформлен')
    
    # Создаем элемент заказа
    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=1,
        price_at_moment=product.price
    )
    
    messages.success(request, f'Товар "{product.title}" добавлен в заказ!')
    return redirect('customer_orders')

@login_required
def customer_orders(request):
    """Страница заказов покупателя"""
    orders = Order.objects.filter(customer=request.user).prefetch_related('items__product')
    return render(request, 'orders/customer_orders.html', {'orders': orders})
