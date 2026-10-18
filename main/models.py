from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Category Name")

    def __str__(self):
        return self.name

class Dish(models.Model):
    name = models.CharField(max_length=100, verbose_name="Dish Name")
    description = models.TextField(verbose_name="Description")
    price = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Price")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='dishes', verbose_name="Category")

    def __str__(self):
        return self.name


class Review(models.Model):
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dish_reviews',
    )
    rating = models.PositiveSmallIntegerField(
        choices=[(value, f'{value} из 5') for value in range(1, 6)],
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Оценка',
    )
    comment = models.TextField(max_length=2000, verbose_name='Отзыв')
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False, verbose_name='Опубликован')

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=('dish', 'user'), name='unique_review_per_user_dish'),
            models.CheckConstraint(condition=models.Q(rating__gte=1, rating__lte=5), name='review_rating_1_to_5'),
        ]

    def __str__(self):
        return f'Отзыв {self.user} о блюде «{self.dish}»'


class Order(models.Model):
    class PaymentMethod(models.TextChoices):
        ONLINE = 'online', 'Онлайн'
        CASH = 'cash', 'Наличными при получении'

    class Status(models.TextChoices):
        NEW = 'new', 'Новый'
        AWAITING_PAYMENT = 'awaiting_payment', 'Ожидает оплаты'
        CONFIRMED = 'confirmed', 'Подтверждён'
        PREPARING = 'preparing', 'Готовится'
        OUT_FOR_DELIVERY = 'out_for_delivery', 'В пути'
        DELIVERED = 'delivered', 'Доставлен'
        CANCELLED = 'cancelled', 'Отменён'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='restaurant_orders',
    )
    customer_name = models.CharField(max_length=120, verbose_name='Имя')
    phone = models.CharField(max_length=32, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Электронная почта')
    delivery_address = models.CharField(max_length=255, verbose_name='Адрес доставки')
    payment_method = models.CharField(
        max_length=16,
        choices=PaymentMethod.choices,
        verbose_name='Способ оплаты',
    )
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.NEW)
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма заказа')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Заказ №{self.pk}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    dish = models.ForeignKey(Dish, on_delete=models.SET_NULL, null=True, blank=True)
    dish_name = models.CharField(max_length=100)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveSmallIntegerField()

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f'{self.dish_name} × {self.quantity}'