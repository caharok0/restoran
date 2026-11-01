from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Dish, Order, Review


class CheckoutForm(forms.Form):
    customer_name = forms.CharField(
        label='Ваше ім’я',
        max_length=120,
        widget=forms.TextInput(attrs={'autocomplete': 'name'}),
    )
    phone = forms.CharField(
        label='Номер телефону',
        max_length=32,
        widget=forms.TextInput(attrs={'autocomplete': 'tel', 'inputmode': 'tel'}),
    )
    email = forms.EmailField(
        label='Електронна пошта (необов’язково)',
        required=False,
        widget=forms.EmailInput(attrs={'autocomplete': 'email'}),
    )
    delivery_address = forms.CharField(
        label='Адреса доставки',
        max_length=255,
        widget=forms.TextInput(attrs={'autocomplete': 'street-address'}),
    )
    payment_method = forms.ChoiceField(
        label='Спосіб оплати',
        choices=Order.PaymentMethod.choices,
        widget=forms.RadioSelect,
        initial=Order.PaymentMethod.CASH,
    )


class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        label='Оцінка',
        choices=[(value, f'{value} ★') for value in range(5, 0, -1)],
        widget=forms.RadioSelect,
    )
    comment = forms.CharField(
        label='Ваш відгук',
        max_length=2000,
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Поділіться враженнями про страву…'}),
    )

    class Meta:
        model = Review
        fields = ('rating', 'comment')


class DishForm(forms.ModelForm):
    class Meta:
        model = Dish
        fields = ('name', 'description', 'price', 'category')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Наприклад, паста з грибами'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Опишіть склад та особливості страви'}),
            'price': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01'}),
        }

class RegistrationForm(UserCreationForm):
    username = forms.CharField(
        required=False,
        max_length=150,
        label='Ім’я користувача (необов’язково)',
    )
    email = forms.EmailField(required=False, label='Електронна пошта (необов’язково)')
    password1 = forms.CharField(label='Пароль', strip=False, widget=forms.PasswordInput)
    password2 = forms.CharField(label='Підтвердження пароля', strip=False, widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Обліковий запис із такою адресою електронної пошти вже існує.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        username = (cleaned_data.get('username') or '').strip()
        email = cleaned_data.get('email') or ''

        if not username and not email:
            self.add_error('username', 'Вкажіть ім’я користувача або адресу електронної пошти.')
            return cleaned_data

        if not username:
            base_username = email[:150]
            username = base_username
            suffix = 1
            while User.objects.filter(username__iexact=username).exists():
                suffix += 1
                suffix_text = str(suffix)
                username = f'{base_username[:150 - len(suffix_text)]}{suffix_text}'
            cleaned_data['username'] = username

        return cleaned_data


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Ім’я користувача або електронна пошта', max_length=254)
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)

    def clean(self):
        identifier = self.cleaned_data.get('username', '').strip()
        if '@' in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
            if user is not None:
                self.cleaned_data['username'] = user.get_username()
        return super().clean()