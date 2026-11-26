from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_alter_order_status_review'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=100, verbose_name='Назва категорії'),
        ),
        migrations.AlterField(
            model_name='dish',
            name='category',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='dishes',
                to='main.category',
                verbose_name='Категорія',
            ),
        ),
        migrations.AlterField(
            model_name='dish',
            name='description',
            field=models.TextField(verbose_name='Опис'),
        ),
        migrations.AlterField(
            model_name='dish',
            name='name',
            field=models.CharField(max_length=100, verbose_name='Назва страви'),
        ),
        migrations.AlterField(
            model_name='dish',
            name='price',
            field=models.DecimalField(max_digits=6, decimal_places=2, verbose_name='Ціна'),
        ),
        migrations.AlterField(
            model_name='order',
            name='customer_name',
            field=models.CharField(max_length=120, verbose_name='Ім’я'),
        ),
        migrations.AlterField(
            model_name='order',
            name='delivery_address',
            field=models.CharField(max_length=255, verbose_name='Адреса доставки'),
        ),
        migrations.AlterField(
            model_name='order',
            name='email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='Електронна пошта'),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(
                choices=[('online', 'Онлайн'), ('cash', 'Готівкою під час отримання')],
                max_length=16,
                verbose_name='Спосіб оплати',
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('new', 'Нове'),
                    ('awaiting_payment', 'Очікує на оплату'),
                    ('confirmed', 'Підтверджено'),
                    ('preparing', 'Готується'),
                    ('out_for_delivery', 'У дорозі'),
                    ('delivered', 'Доставлено'),
                    ('cancelled', 'Скасовано'),
                ],
                default='new',
                max_length=24,
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='total',
            field=models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сума замовлення'),
        ),
        migrations.AlterField(
            model_name='review',
            name='comment',
            field=models.TextField(max_length=2000, verbose_name='Відгук'),
        ),
        migrations.AlterField(
            model_name='review',
            name='is_approved',
            field=models.BooleanField(default=False, verbose_name='Опубліковано'),
        ),
        migrations.AlterField(
            model_name='review',
            name='rating',
            field=models.PositiveSmallIntegerField(
                choices=[(value, f'{value} з 5') for value in range(1, 6)],
                validators=[MinValueValidator(1), MaxValueValidator(5)],
                verbose_name='Оцінка',
            ),
        ),
    ]
