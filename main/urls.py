from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dish/<int:dish_id>/', views.dish_detail, name='dish_detail'),
]