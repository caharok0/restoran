import django.core.validators
from django.db import migrations, models
import main.models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_ukrainian_labels'),
    ]

    operations = [
        migrations.AddField(
            model_name='dish',
            name='image',
            field=models.ImageField(
                blank=True,
                help_text='JPG, PNG, WebP або GIF; до 5 МБ.',
                upload_to='dishes/',
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=('jpg', 'jpeg', 'png', 'webp', 'gif'),
                    ),
                    main.models.validate_dish_image_size,
                ],
                verbose_name='Завантажити фото',
            ),
        ),
        migrations.AddField(
            model_name='dish',
            name='image_url',
            field=models.URLField(
                blank=True,
                help_text='Вставте пряме посилання на фото з http:// або https://.',
                max_length=1000,
                validators=[django.core.validators.URLValidator(schemes=('http', 'https'))],
                verbose_name='Посилання на фото',
            ),
        ),
    ]