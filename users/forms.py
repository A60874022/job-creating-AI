from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserChangeForm
from .models import User, Profile

class UserRegistrationForm(UserCreationForm):
    """
    Форма регистрации пользователя.
    Наследуется от UserCreationForm, которая предоставляет логику для паролей.
    """
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('your.email@example.com'),
            'autocomplete': 'email'
        }),
        help_text=_('Enter a valid email address.')
    )
    
    is_master = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label=_('I am a master'),
        help_text=_('Check this if you want to sell your products.')
    )

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2', 'is_master')
        
    def clean_email(self):
        """Валидация email на уникальность"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(_('A user with this email already exists.'))
        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Кастомизация полей паролей
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})


from django.contrib.auth.forms import AuthenticationForm

class UserLoginForm(AuthenticationForm):
    """
    Форма входа пользователя.
    Наследуется от AuthenticationForm, меняем username на email.
    """
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('your.email@example.com'),
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Password'),
            'autocomplete': 'current-password'
        })
    )
    
    error_messages = {
        'invalid_login': _(
            "Please enter a correct %(username)s and password. "
            "Note that both fields may be case-sensitive."
        ),
        'inactive': _("This account is inactive."),
    }


class UserEditForm(UserChangeForm):
    # Убираем поле password, чтобы пользователь не видел его в открытом виде
    password = None

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name') # Добавляем поля при необходимости

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('avatar', 'bio', 'city')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Расскажите о себе и своем творчестве...'}),
            'city': forms.TextInput(attrs={'placeholder': 'Ваш город'}),
        }
        labels = {
            'avatar': 'Аватар профиля',
            'bio': 'О себе',
            'city': 'Город',
        }