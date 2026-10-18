from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Order, Review


class CheckoutForm(forms.Form):
    customer_name = forms.CharField(
        label='Ваше имя',
        max_length=120,
        widget=forms.TextInput(attrs={'autocomplete': 'name'}),
    )
    phone = forms.CharField(
        label='Номер телефона',
        max_length=32,
        widget=forms.TextInput(attrs={'autocomplete': 'tel', 'inputmode': 'tel'}),
    )
    email = forms.EmailField(
        label='Электронная почта (необязательно)',
        required=False,
        widget=forms.EmailInput(attrs={'autocomplete': 'email'}),
    )
    delivery_address = forms.CharField(
        label='Адрес доставки',
        max_length=255,
        widget=forms.TextInput(attrs={'autocomplete': 'street-address'}),
    )
    payment_method = forms.ChoiceField(
        label='Способ оплаты',
        choices=Order.PaymentMethod.choices,
        widget=forms.RadioSelect,
        initial=Order.PaymentMethod.CASH,
    )


class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        label='Оценка',
        choices=[(value, f'{value} ★') for value in range(5, 0, -1)],
        widget=forms.RadioSelect,
    )
    comment = forms.CharField(
        label='Ваш отзыв',
        max_length=2000,
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Поделитесь впечатлениями о блюде…'}),
    )

    class Meta:
        model = Review
        fields = ('rating', 'comment')

class RegistrationForm(UserCreationForm):
    username = forms.CharField(
        required=False,
        max_length=150,
        label='Имя пользователя (необязательно)',
    )
    email = forms.EmailField(required=False, label='Электронная почта (необязательно)')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Аккаунт с таким адресом электронной почты уже существует.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        username = (cleaned_data.get('username') or '').strip()
        email = cleaned_data.get('email') or ''

        if not username and not email:
            self.add_error('username', 'Укажите имя пользователя или адрес электронной почты.')
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
    username = forms.CharField(label='Имя пользователя или электронная почта', max_length=254)
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)

    def clean(self):
        identifier = self.cleaned_data.get('username', '').strip()
        if '@' in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
            if user is not None:
                self.cleaned_data['username'] = user.get_username()
        return super().clean()