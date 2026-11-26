from django.db import migrations


DISHES = [
    ('Гамбургер', 'Соковита котлета з сиром і овочами у булочці.', '12.50'),
    ('Хот-дог', 'Сосиска в булочці з кетчупом і цибулею.', '8.50'),
    ('Курячі крильця', 'Гострі крильця в хрусткій паніровці.', '14.00'),
    ('Кламат чаудер', 'Кремова юшка з молюсками та картоплею.', '11.50'),
    ('Біф бургер', 'Бургер із яловичиною, сиром і соусом барбекю.', '13.50'),
    ('Мак-енд-чіз', 'Макаронні вироби із густим сирним соусом.', '9.50'),
    ('Спагеті з фрикадельками', 'Паста з м’ясними фрикадельками в томатному соусі.', '12.00'),
    ('Пібургер', 'Бургер із фаршу та гострим сальсою.', '13.00'),
    ('Рибний фіш-ен-чіпс', 'Смажена риба з хрусткою картоплею фрі.', '15.00'),
    ('Яблучний пиріг', 'Теплий пиріг із яблуками та корицею.', '7.50'),
]


def seed_dishes(apps, schema_editor):
    Category = apps.get_model('main', 'Category')
    Dish = apps.get_model('main', 'Dish')

    category, _ = Category.objects.get_or_create(name='Американська кухня')
    for name, description, price in DISHES:
        Dish.objects.get_or_create(
            name=name,
            defaults={
                'description': description,
                'price': price,
                'category': category,
            },
        )


def remove_dishes(apps, schema_editor):
    Category = apps.get_model('main', 'Category')
    Dish = apps.get_model('main', 'Dish')

    Dish.objects.filter(name__in=[dish[0] for dish in DISHES]).delete()
    Category.objects.filter(name='Американська кухня', dishes__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0007_https_dish_image_urls'),
    ]

    operations = [
        migrations.RunPython(seed_dishes, remove_dishes),
    ]
