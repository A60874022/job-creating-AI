import logging
import os
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, UpdateView, ListView, DeleteView, DetailView
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q

from .forms import ProductForm, ProductImageFormSet
from .models import Product, Category, Favorite
from orders.models import Order

logger = logging.getLogger(__name__)

class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:my_products')
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                form.instance.master = self.request.user
                response = super().form_valid(form)
                
                formset = ProductImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
                if formset.is_valid():
                    formset.save()
                    if not self.object.images.filter(is_main=True).exists():
                        first_image = self.object.images.first()
                        if first_image:
                            first_image.is_main = True
                            first_image.save()
                else:
                    # Логируем только реальные ошибки
                    for form in formset:
                        if form.errors:
                            logger.error(
                                "Image validation errors for product %s: %s", 
                                self.object.id, form.errors
                            )
                            for field, errors in form.errors.items():
                                for error in errors:
                                    messages.error(self.request, f"Ошибка в изображении: {error}")
            
            return response
            
        except Exception as e:
            logger.error("Product creation failed: %s", str(e), exc_info=True)
            messages.error(self.request, 'Ошибка при создании товара')
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = ProductImageFormSet(self.request.POST, self.request.FILES)
        else:
            context['formset'] = ProductImageFormSet()
        return context

class ProductUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:my_products')
    
    def test_func(self):
        product = self.get_object()
        return self.request.user == product.master
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                response = super().form_valid(form)
                formset = ProductImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
                
                if formset.is_valid():
                    formset.save()
                else:
                    for form in formset:
                        if form.errors:
                            logger.error(
                                "Image update errors for product %s: %s",
                                self.object.id, form.errors
                            )
                            for field, errors in form.errors.items():
                                for error in errors:
                                    messages.error(self.request, f"Ошибка в изображении: {error}")
            
            return response
            
        except Exception as e:
            logger.error("Product update failed for product %s: %s", self.get_object().id, str(e), exc_info=True)
            messages.error(self.request, 'Ошибка при обновлении товара')
            return self.form_invalid(form)

class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    success_url = reverse_lazy('products:my_products')
    template_name = 'products/product_confirm_delete.html'
    
    def get_queryset(self):
        return Product.objects.filter(master=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        try:
            product = self.get_object()
            result = super().delete(request, *args, **kwargs)
            messages.success(request, 'Товар успешно удален!')
            return result
        except Exception as e:
            logger.error("Product deletion failed for product %s: %s", self.get_object().id, str(e), exc_info=True)
            messages.error(request, 'Ошибка при удалении товара')
            return redirect('products:my_products')

class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'products/my_products.html'
    context_object_name = 'products'
    
    def get_queryset(self):
        return Product.objects.filter(master=self.request.user).order_by('-created_at')

class ProductCatalogView(ListView):
    model = Product
    template_name = 'products/catalog.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        try:
            queryset = Product.objects.filter(is_active=True).select_related('master', 'category')
            
            category_slug = self.request.GET.get('category')
            if category_slug:
                category = get_object_or_404(Category, slug=category_slug)
                queryset = queryset.filter(category=category)
            
            search_query = self.request.GET.get('q')
            if search_query:
                queryset = queryset.filter(
                    Q(title__icontains=search_query) |
                    Q(description__icontains=search_query)
                )
            
            return queryset.order_by('-created_at')
            
        except Exception as e:
            logger.error("Error loading product catalog: %s", str(e), exc_info=True)
            return Product.objects.none()
    
    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            context['categories'] = Category.objects.all()
            context['selected_category'] = self.request.GET.get('category', '')
            context['search_query'] = self.request.GET.get('q', '')
            
            if self.request.user.is_authenticated:
                user_favorites = Favorite.objects.filter(
                    user=self.request.user
                ).values_list('product_id', flat=True)
                context['user_favorites'] = set(user_favorites)
            else:
                context['user_favorites'] = set()
                
            return context
            
        except Exception as e:
            logger.error("Error preparing catalog context: %s", str(e), exc_info=True)
            return super().get_context_data(**kwargs)

class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    
    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('master')
    
    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            product = self.object
            
            if self.request.user.is_authenticated:
                context['is_in_favorites'] = Favorite.objects.filter(
                    user=self.request.user, 
                    product=product
                ).exists()
                context['is_own_product'] = product.master == self.request.user
            else:
                context['is_in_favorites'] = False
                context['is_own_product'] = False
                
            return context
            
        except Exception as e:
            logger.error("Error preparing product detail context for product %s: %s", 
                        self.object.id, str(e), exc_info=True)
            return super().get_context_data(**kwargs)

@login_required
def profile(request):
    """Главная страница профиля мастера с вкладками"""
    try:
        active_tab = request.GET.get('tab', 'orders')
        
        context = {
            'active_tab': active_tab,
        }
        
        if active_tab == 'orders':
            # Показываем заказы как покупателя
            context['orders'] = Order.objects.filter(customer=request.user).prefetch_related('items__product')
        elif active_tab == 'favorites':
            context['favorites'] = Favorite.objects.filter(user=request.user).select_related('product')
        elif active_tab == 'my_products':
            # Показываем товары мастера
            context['my_products'] = Product.objects.filter(master=request.user).order_by('-created_at')
        elif active_tab == 'master_orders':
            # Показываем заказы на товары мастера
            context['master_orders'] = Order.objects.filter(items__product__master=request.user).distinct()
        
        return render(request, 'users/customer_profile.html', context)
        
    except Exception as e:
        logger.error("Error loading profile for user %s: %s", 
                    request.user.id, str(e), exc_info=True)
        messages.error(request, "Ошибка при загрузке профиля")
        return redirect('products:catalog')

@login_required
def add_to_favorites(request, product_id):
    """Добавление товара в избранное"""
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # УБРАНА ПРОВЕРКА: if product.master == request.user:
        # Теперь мастер может добавлять в избранное любые товары, включая свои
        
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if created:
            messages.success(request, f'Товар "{product.title}" добавлен в избранное')
        else:
            messages.info(request, f'Товар "{product.title}" уже в избранном')
        
        return redirect(request.META.get('HTTP_REFERER', 'catalog'))
    
    except Exception as e:
        logger.error("Add to favorites failed for product %s by user %s: %s", 
                    product_id, request.user.id, str(e), exc_info=True)
        messages.error(request, 'Ошибка при добавлении в избранное')
        return redirect('products:catalog')

@login_required
def remove_from_favorites(request, favorite_id):
    """Удаление товара из избранного"""
    try:
        favorite = get_object_or_404(Favorite, id=favorite_id, user=request.user)
        product_title = favorite.product.title
        favorite.delete()
        
        messages.success(request, f'Товар "{product_title}" удален из избранного')
        return redirect(f"{reverse('products:profile')}?tab=favorites")
    
    except Exception as e:
        logger.error("Remove favorite failed for favorite %s by user %s: %s", 
                    favorite_id, request.user.id, str(e), exc_info=True)
        messages.error(request, 'Ошибка при удалении из избранного')
        return redirect('products:profile')

@login_required
def remove_from_favorites_by_product(request, product_id):
    """Удаление товара из избранного по product_id"""
    try:
        product = get_object_or_404(Product, id=product_id)
        favorite = get_object_or_404(Favorite, user=request.user, product=product)
        product_title = favorite.product.title
        favorite.delete()
        
        messages.success(request, f'Товар "{product_title}" удален из избранного')
        return redirect(request.META.get('HTTP_REFERER', 'catalog'))
    
    except Exception as e:
        logger.error("Remove favorite by product failed for product %s by user %s: %s", 
                    product_id, request.user.id, str(e), exc_info=True)
        messages.error(request, 'Ошибка при удалении из избранного')
        return redirect(request.META.get('HTTP_REFERER', 'products:catalog'))