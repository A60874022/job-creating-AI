from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, UpdateView, ListView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .forms import ProductForm, ProductImageFormSet
from .models import Product, Category  # Добавляем импорт Category


from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, UpdateView, ListView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from .forms import ProductForm, ProductImageFormSet
from .models import Product, Category, Favorite

class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:my_products')
    
    def form_valid(self, form):
        form.instance.master = self.request.user
        response = super().form_valid(form)
        
        formset = ProductImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        if formset.is_valid():
            formset.save()
            # Убеждаемся, что есть хотя бы одно основное изображение
            if not self.object.images.filter(is_main=True).exists():
                first_image = self.object.images.first()
                if first_image:
                    first_image.is_main = True
                    first_image.save()
        else:
            # Если форма изображений невалидна, добавляем ошибки
            for form in formset:
                for error in form.errors:
                    messages.error(self.request, f"Ошибка в изображении: {error}")
        
        return response
    
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
        response = super().form_valid(form)
        formset = ProductImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        if formset.is_valid():
            formset.save()
        else:
            for form in formset:
                for error in form.errors:
                    messages.error(self.request, f"Ошибка в изображении: {error}")
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = ProductImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            # Замечание 22: Убедимся, что форма отображает существующие изображения
            context['formset'] = ProductImageFormSet(instance=self.object)
        return context


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    success_url = reverse_lazy('products:my_products')
    template_name = 'products/product_confirm_delete.html'
    
    def get_queryset(self):
        """Ограничиваем удаление только своими товарами"""
        return Product.objects.filter(master=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Товар успешно удален!')
        return super().delete(request, *args, **kwargs)

class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'products/my_products.html'
    context_object_name = 'products'
    
    def get_queryset(self):
        # Показываем только товары текущего пользователя
        return Product.objects.filter(master=self.request.user).order_by('-created_at')


from django.views.generic import ListView
from django.db.models import Q
from django.shortcuts import get_object_or_404

# Добавляем к существующим импортам
class ProductCatalogView(ListView):
    model = Product
    template_name = 'products/catalog.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('master', 'category')
        
        # Фильтрация по категории
        category_slug = self.request.GET.get('category')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            queryset = queryset.filter(category=category)
        
        # Поиск по названию
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['selected_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('q', '')
        
        # Добавляем информацию об избранных товарах пользователя
        if self.request.user.is_authenticated:
            user_favorites = Favorite.objects.filter(
                user=self.request.user
            ).values_list('product_id', flat=True)
            context['user_favorites'] = set(user_favorites)
        else:
            context['user_favorites'] = set()
            
        return context



from django.views.generic import DetailView
from django.contrib import messages
from django.shortcuts import get_object_or_404

# Добавляем к существующим импортам
class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    
    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('master')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        
        # Проверяем, добавлен ли товар в избранное текущего пользователя
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



from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from products.models import Product, Favorite
from orders.models import Order

@login_required
def customer_profile(request):
    """Главная страница ЛК покупателя с вкладками"""
    active_tab = request.GET.get('tab', 'orders')
    
    context = {
        'active_tab': active_tab,
    }
    
    # Загружаем данные в зависимости от активной вкладки
    if active_tab == 'orders':
        context['orders'] = Order.objects.filter(customer=request.user).prefetch_related('items__product')
    elif active_tab == 'favorites':
        context['favorites'] = Favorite.objects.filter(user=request.user).select_related('product')
    elif active_tab == 'dialogs':
        # Заглушка для диалогов - реализуем в следующем этапе
        context['dialogs'] = []
    
    return render(request, 'users/customer_profile.html', context)

@login_required
def add_to_favorites(request, product_id):
    """Добавление товара в избранное"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    # Замечание 16: Запрещаем добавлять собственные товары
    if product.master == request.user:
        messages.error(request, 'Вы не можете добавить в избранное свой собственный товар')
        return redirect(request.META.get('HTTP_REFERER', 'catalog'))
    
    # Проверяем, нет ли уже в избранном
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if created:
        messages.success(request, f'Товар "{product.title}" добавлен в избранное')
    else:
        messages.info(request, f'Товар "{product.title}" уже в избранном')
    
    return redirect(request.META.get('HTTP_REFERER', 'catalog'))

@login_required
def remove_from_favorites(request, favorite_id):
    """Удаление товара из избранного"""
    favorite = get_object_or_404(Favorite, id=favorite_id, user=request.user)
    product_title = favorite.product.title
    favorite.delete()
    
    messages.success(request, f'Товар "{product_title}" удален из избранного')
    # Корректный редирект с параметрами
    return redirect(f"{reverse('products:customer_profile')}?tab=favorites")


@login_required
def remove_from_favorites_by_product(request, product_id):
    """Удаление товара из избранного по product_id"""
    product = get_object_or_404(Product, id=product_id)
    favorite = get_object_or_404(Favorite, user=request.user, product=product)
    product_title = favorite.product.title
    favorite.delete()
    
    messages.success(request, f'Товар "{product_title}" удален из избранного')
    return redirect(request.META.get('HTTP_REFERER', 'catalog'))