from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import login, logout
from django.contrib.auth.views import redirect_to_login
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .cart import Cart
from .forms import CheckoutForm, DishForm, LoginForm, RegistrationForm, ReviewForm
from .models import Dish, Order, OrderItem, Review


def index(request):
    dishes = Dish.objects.select_related('category').annotate(
        average_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
        review_count=Count('reviews', filter=Q(reviews__is_approved=True)),
    )
    return render(request, 'index.html', {'dishes': dishes})


@user_passes_test(lambda user: user.is_staff, login_url='login')
def menu_management(request):
    dishes = Dish.objects.select_related('category').order_by('category__name', 'name')
    return render(request, 'menu_management.html', {'dishes': dishes})


@user_passes_test(lambda user: user.is_staff, login_url='login')
def dish_edit(request, dish_id=None):
    dish = get_object_or_404(Dish, pk=dish_id) if dish_id is not None else None
    if request.method == 'POST':
        form = DishForm(request.POST, instance=dish)
        if form.is_valid():
            form.save()
            message = 'Страву оновлено.' if dish is not None else 'Страву додано до меню.'
            messages.success(request, message)
            return redirect('menu_management')
    else:
        form = DishForm(instance=dish)
    return render(request, 'dish_manage_form.html', {
        'form': form,
        'dish': dish,
    })


@user_passes_test(lambda user: user.is_staff, login_url='login')
@require_POST
def dish_delete(request, dish_id):
    dish = get_object_or_404(Dish, pk=dish_id)
    dish_name = dish.name
    dish.delete()
    messages.success(request, f'Страву «{dish_name}» видалено з меню.')
    return redirect('menu_management')


def _cart_totals(items):
    item_count = sum(item['quantity'] for item in items)
    total = sum((item['total_price'] for item in items), start=Decimal('0.00'))
    return item_count, total


def dish_detail(request, dish_id):
    dish = get_object_or_404(Dish.objects.select_related('category'), pk=dish_id)
    own_review = None
    if request.user.is_authenticated:
        own_review = Review.objects.filter(dish=dish, user=request.user).first()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), reverse('login'))
        review_form = ReviewForm(request.POST, instance=own_review)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.dish = dish
            review.user = request.user
            review.is_approved = True
            review.save()
            messages.success(request, 'Дякуємо! Ваш відгук опубліковано.')
            return redirect('dish_detail', dish_id=dish.pk)
        messages.error(request, 'Перевірте оцінку та текст відгуку.')
    else:
        review_form = ReviewForm(instance=own_review)

    approved_reviews = Review.objects.filter(dish=dish, is_approved=True).select_related('user')
    visible_reviews = approved_reviews
    if request.user.is_authenticated:
        visible_reviews = Review.objects.filter(dish=dish).filter(
            Q(is_approved=True) | Q(user=request.user)
        ).select_related('user')
    rating_summary = approved_reviews.aggregate(
        average=Avg('rating'),
        count=Count('id'),
    )
    return render(request, 'dish_detail.html', {
        'dish': dish,
        'reviews': visible_reviews,
        'average_rating': rating_summary['average'],
        'review_count': rating_summary['count'],
        'own_review': own_review,
        'review_form': review_form,
    })


def cart_detail(request):
    cart = Cart(request)
    cart_items = list(cart)
    item_count, cart_total = _cart_totals(cart_items)
    checkout_form = CheckoutForm(initial={
        'customer_name': request.user.get_full_name() if request.user.is_authenticated else '',
        'email': request.user.email if request.user.is_authenticated else '',
    })
    return render(request, 'cart.html', {
        'cart': cart,
        'cart_items': cart_items,
        'item_count': item_count,
        'cart_total': cart_total,
        'checkout_form': checkout_form,
        'has_items': bool(cart_items),
    })


def _cart_json(request, message):
    cart = Cart(request)
    cart_items = list(cart)
    item_count, total = _cart_totals(cart_items)
    html = render_to_string('cart_items.html', {'cart_items': cart_items}, request=request)
    return JsonResponse({
        'ok': True,
        'message': message,
        'items_html': html,
        'item_count': item_count,
        'total': str(total),
        'has_items': bool(cart_items),
    })


def _expects_json(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def _cart_redirect(request):
    target = request.POST.get('next', '')
    if target and url_has_allowed_host_and_scheme(target, {request.get_host()}):
        return redirect(target)
    return redirect('cart_detail')


@require_POST
def cart_add(request, dish_id):
    dish = get_object_or_404(Dish, pk=dish_id)
    try:
        quantity = int(request.POST.get('quantity', 1))
        Cart(request).add(dish, quantity=quantity)
    except (TypeError, ValueError) as error:
        message = str(error) or 'Вкажіть коректну кількість.'
        if _expects_json(request):
            return JsonResponse({'ok': False, 'message': message}, status=400)
        messages.error(request, message)
    else:
        message = f'«{dish.name}» додано до кошика.'
        if _expects_json(request):
            return _cart_json(request, message)
        messages.success(request, message)
    return _cart_redirect(request)


@require_POST
def cart_update(request, dish_id):
    dish = get_object_or_404(Dish, pk=dish_id)
    try:
        quantity = int(request.POST.get('quantity', 0))
        Cart(request).add(dish, quantity=quantity, update_quantity=True)
    except (TypeError, ValueError) as error:
        message = str(error) or 'Вкажіть коректну кількість.'
        if _expects_json(request):
            return JsonResponse({'ok': False, 'message': message}, status=400)
        messages.error(request, message)
    else:
        if _expects_json(request):
            return _cart_json(request, 'Кошик оновлено.')
    return redirect('cart_detail')


@require_POST
def cart_remove(request, dish_id):
    dish = get_object_or_404(Dish, pk=dish_id)
    Cart(request).remove(dish)
    message = f'«{dish.name}» видалено з кошика.'
    if _expects_json(request):
        return _cart_json(request, message)
    messages.success(request, message)
    return redirect('cart_detail')


def checkout(request):
    if request.method != 'POST':
        return redirect('cart_detail')

    cart = Cart(request)
    cart_items = list(cart)
    if not cart_items:
        messages.error(request, 'Кошик порожній — додайте страви перед оформленням замовлення.')
        return redirect('cart_detail')

    form = CheckoutForm(request.POST)
    if not form.is_valid():
        item_count, cart_total = _cart_totals(cart_items)
        return render(request, 'cart.html', {
            'cart': cart,
            'cart_items': cart_items,
            'item_count': item_count,
            'cart_total': cart_total,
            'checkout_form': form,
            'has_items': True,
        })

    total = sum((item['total_price'] for item in cart_items), start=Decimal('0.00'))
    payment_method = form.cleaned_data['payment_method']
    status = (
        Order.Status.AWAITING_PAYMENT
        if payment_method == Order.PaymentMethod.ONLINE
        else Order.Status.NEW
    )
    with transaction.atomic():
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            customer_name=form.cleaned_data['customer_name'],
            phone=form.cleaned_data['phone'],
            email=form.cleaned_data['email'],
            delivery_address=form.cleaned_data['delivery_address'],
            payment_method=payment_method,
            status=status,
            total=total,
        )
        OrderItem.objects.bulk_create([
            OrderItem(
                order=order,
                dish=item['dish'],
                dish_name=item['dish'].name,
                unit_price=item['price'],
                quantity=item['quantity'],
            )
            for item in cart_items
        ])

    cart.clear()
    request.session['last_order_id'] = order.pk
    messages.success(request, f'Замовлення №{order.pk} успішно оформлено.')
    return redirect('order_success', order_id=order.pk)


def order_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    is_owner = request.user.is_authenticated and order.user_id == request.user.pk
    if request.session.get('last_order_id') != order.pk and not is_owner:
        return redirect('index')
    request.session.pop('last_order_id', None)
    return render(request, 'order_success.html', {'order': order})


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Реєстрацію успішно завершено.')
            return redirect('index')
        messages.error(request, 'Не вдалося зареєструватися. Перевірте введені дані.')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            login(request, form.get_user())
            messages.success(request, f'Вітаємо, {username}!')
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
                return redirect(next_url)
            return redirect('index')
        messages.error(request, 'Неправильне ім’я користувача, адреса електронної пошти або пароль.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form, 'next': request.GET.get('next', '')})

def logout_view(request):
    logout(request)
    messages.success(request, 'Ви вийшли з облікового запису.')
    return redirect('login')
