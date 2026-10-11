from django.shortcuts import render
from .models import Dish

def index(request):
    dishes = Dish.objects.all()
    return render(request, 'index.html', {'dishes': dishes})

def dish_detail(request, dish_id):
    dish = Dish.objects.get(id=dish_id)
    return render(request, 'dish_detail.html', {'dish': dish})