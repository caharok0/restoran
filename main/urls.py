from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dish/<int:dish_id>/', views.dish_detail, name='dish_detail'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:dish_id>/', views.cart_add, name='cart_add'),
    path('cart/update/<int:dish_id>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:dish_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/<int:order_id>/success/', views.order_success, name='order_success'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]