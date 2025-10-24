from django import forms
from django.core.validators import MinValueValidator, RegexValidator
from .models import Product, ProductImage

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'title', 'description', 'price']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Вязаная шерстяная шапка'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Опишите ваш товар, материалы, размеры...'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'min': '1',
                'step': '1'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Замечание 18: Добавляем валидаторы для кириллицы
        self.fields['title'].validators.append(
            RegexValidator(
                regex='^[а-яА-ЯёЁ0-9\s\-\!\.\(\)]+$',
                message='Название должно содержать только кириллические символы, цифры и пробелы'
            )
        )
        self.fields['description'].validators.append(
            RegexValidator(
                regex='^[а-яА-ЯёЁ0-9\s\-\!\.\(\)\,\:\;]+$',
                message='Описание должно содержать только кириллические символы, цифры и знаки препинания'
            )
        )
        # Замечание 19: Добавляем валидатор цены
        self.fields['price'].validators.append(
            MinValueValidator(1, message='Цена должна быть не менее 1 рубля')
        )
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price and price < 1:
            raise forms.ValidationError('Цена должна быть не менее 1 рубля')
        # Замечание 19: Округляем до целых чисел
        if price:
            return round(price)
        return price

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'is_main']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_main': forms.CheckboxInput(attrs={'class': 'form-check-input main-image-checkbox'}),
        }

# Замечание 20: Уточняем количество фото (включительно до 4)
ProductImageFormSet = forms.inlineformset_factory(
    Product,
    ProductImage,
    form=ProductImageForm,
    extra=4,  # Можно загрузить до 4 фото включительно
    can_delete=True,
    max_num=4,  # Максимум 4 фото
)