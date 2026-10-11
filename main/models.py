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