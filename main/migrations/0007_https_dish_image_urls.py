import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_dish_images'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dish',
            name='image_url',
            field=models.URLField(
                blank=True,
                help_text='Вставте пряме HTTPS-посилання на фото.',
                max_length=1000,
                validators=[django.core.validators.URLValidator(schemes=('https',))],
                verbose_name='HTTPS-посилання на фото',
            ),
        ),
    ]