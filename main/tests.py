from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal

from .cart import Cart
from .models import Category, Dish, Order, OrderItem, Review


class RegistrationAndLoginTests(TestCase):
	def test_register_with_username_without_email(self):
		response = self.client.post('/register/', {
			'username': 'username_only',
			'email': '',
			'password1': 'SafePassword_726!',
			'password2': 'SafePassword_726!',
		})

		self.assertRedirects(response, '/')
		user = User.objects.get(username='username_only')
		self.assertEqual(user.email, '')

	def test_register_with_email_without_username(self):
		response = self.client.post('/register/', {
			'username': '',
			'email': 'person@example.com',
			'password1': 'SafePassword_726!',
			'password2': 'SafePassword_726!',
		})

		self.assertRedirects(response, '/')
		user = User.objects.get(email='person@example.com')
		self.assertEqual(user.username, 'person@example.com')

	def test_registration_requires_username_or_email(self):
		response = self.client.post('/register/', {
			'username': '',
			'email': '',
			'password1': 'SafePassword_726!',
			'password2': 'SafePassword_726!',
		})

		self.assertEqual(response.status_code, 200)
		self.assertFalse(User.objects.exists())
		self.assertContains(response, 'Укажите имя пользователя или адрес электронной почты.')

	def test_login_with_email(self):
		User.objects.create_user(
			username='email_login_user',
			email='person@example.com',
			password='SafePassword_726!',
		)

		response = self.client.post('/login/', {
			'username': 'PERSON@example.com',
			'password': 'SafePassword_726!',
		})

		self.assertRedirects(response, '/')
		self.assertTrue(response.wsgi_request.user.is_authenticated)


class ShoppingCartTests(TestCase):
	def setUp(self):
		self.category = Category.objects.create(name='Горячее')
		self.dish = Dish.objects.create(
			name='Тестовое блюдо',
			description='Описание',
			price=Decimal('12.50'),
			category=self.category,
		)

	def test_add_accumulates_quantity_and_calculates_total(self):
		cart = Cart(self.client)
		cart.add(self.dish, quantity=2)
		cart.add(self.dish, quantity=1)

		item = list(cart)[0]
		self.assertEqual(item['quantity'], 3)
		self.assertEqual(item['total_price'], Decimal('37.50'))
		self.assertEqual(cart.total_price, Decimal('37.50'))

	def test_add_view_renders_in_cart(self):
		response = self.client.post(f'/cart/add/{self.dish.pk}/', {'quantity': '2'})

		self.assertRedirects(response, '/cart/')
		cart_response = self.client.get('/cart/')
		self.assertContains(cart_response, 'Тестовое блюдо')
		self.assertContains(cart_response, '25,00 ₽')

	def test_remove_view_removes_item(self):
		self.client.post(f'/cart/add/{self.dish.pk}/', {'quantity': '1'})
		response = self.client.post(f'/cart/remove/{self.dish.pk}/')

		self.assertRedirects(response, '/cart/')
		self.assertContains(self.client.get('/cart/'), 'В корзине пока пусто')

	def test_update_view_replaces_quantity(self):
		self.client.post(f'/cart/add/{self.dish.pk}/', {'quantity': '2'})
		response = self.client.post(f'/cart/update/{self.dish.pk}/', {'quantity': '4'})

		self.assertRedirects(response, '/cart/')
		cart = Cart(self.client)
		self.assertEqual(list(cart)[0]['quantity'], 4)
		self.assertEqual(cart.total_price, Decimal('50.00'))

	def test_clear_empties_session_cart(self):
		cart = Cart(self.client)
		cart.add(self.dish, quantity=2)
		cart.clear()

		self.assertEqual(list(cart), [])
		self.assertEqual(cart.total_price, Decimal('0.00'))

	def test_checkout_creates_order_and_clears_cart(self):
		self.client.post(f'/cart/add/{self.dish.pk}/', {'quantity': '2'})
		response = self.client.post('/checkout/', {
			'customer_name': 'Анна',
			'phone': '+79990000000',
			'email': 'anna@example.com',
			'delivery_address': 'Москва, улица Тестовая, 1',
			'payment_method': Order.PaymentMethod.CASH,
		})

		order = Order.objects.get()
		self.assertRedirects(response, f'/order/{order.pk}/success/', fetch_redirect_response=False)
		self.assertEqual(order.total, Decimal('25.00'))
		self.assertEqual(order.items.get().quantity, 2)
		self.assertEqual(order.items.get().dish_name, self.dish.name)
		self.assertEqual(self.client.session.get('cart', {}), {})
		self.assertContains(self.client.get(response.url), 'Заказ №')

	def test_online_checkout_is_saved_as_awaiting_payment(self):
		self.client.post(f'/cart/add/{self.dish.pk}/', {'quantity': '1'})
		self.client.post('/checkout/', {
			'customer_name': 'Анна',
			'phone': '+79990000000',
			'delivery_address': 'Москва, улица Тестовая, 1',
			'payment_method': Order.PaymentMethod.ONLINE,
		})

		order = Order.objects.get()
		self.assertEqual(order.status, Order.Status.AWAITING_PAYMENT)

	def test_invalid_checkout_does_not_create_order_or_clear_cart(self):
		self.client.post(f'/cart/add/{self.dish.pk}/', {'quantity': '1'})
		response = self.client.post('/checkout/', {
			'customer_name': '',
			'phone': '',
			'delivery_address': '',
			'payment_method': Order.PaymentMethod.CASH,
		})

		self.assertEqual(response.status_code, 200)
		self.assertFalse(Order.objects.exists())
		self.assertTrue(self.client.session.get('cart'))
		self.assertContains(response, 'Обязательное поле')

	def test_empty_cart_cannot_be_checked_out(self):
		response = self.client.post('/checkout/', {
			'customer_name': 'Анна',
			'phone': '+79990000000',
			'delivery_address': 'Москва, улица Тестовая, 1',
			'payment_method': Order.PaymentMethod.CASH,
		})

		self.assertRedirects(response, '/cart/')
		self.assertFalse(Order.objects.exists())

	def test_cart_mutation_supports_ajax(self):
		response = self.client.post(
			f'/cart/add/{self.dish.pk}/',
			{'quantity': '2'},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)

		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertTrue(payload['ok'])
		self.assertEqual(payload['item_count'], 2)
		self.assertIn('Тестовое блюдо', payload['items_html'])

	def test_add_rejects_non_positive_quantity(self):
		self.client.post(f'/cart/add/{self.dish.pk}/', {'quantity': '0'})

		self.assertEqual(self.client.session.get('cart', {}), {})

	def test_get_does_not_mutate_cart(self):
		response = self.client.get(f'/cart/add/{self.dish.pk}/')

		self.assertEqual(response.status_code, 405)
		self.assertEqual(self.client.session.get('cart', {}), {})


class DishReviewTests(TestCase):
	def setUp(self):
		self.category = Category.objects.create(name='Горячее')
		self.dish = Dish.objects.create(
			name='Тестовое блюдо',
			description='Описание',
			price=Decimal('12.50'),
			category=self.category,
		)
		self.user = User.objects.create_user(username='reviewer', password='SafePassword_726!')

	def test_review_submission_requires_login(self):
		response = self.client.post(
			f'/dish/{self.dish.pk}/',
			{'rating': '5', 'comment': 'Отличное блюдо'},
		)

		self.assertRedirects(response, f'/login/?next=/dish/{self.dish.pk}/', fetch_redirect_response=False)
		self.assertFalse(Review.objects.exists())

	def test_submitted_review_is_private_until_moderated(self):
		self.client.force_login(self.user)
		response = self.client.post(
			f'/dish/{self.dish.pk}/',
			{'rating': '5', 'comment': 'Отличное блюдо'},
		)

		self.assertRedirects(response, f'/dish/{self.dish.pk}/')
		review = Review.objects.get()
		self.assertFalse(review.is_approved)
		self.assertContains(self.client.get(f'/dish/{self.dish.pk}/'), 'Отличное блюдо')
		self.assertContains(self.client.get(f'/dish/{self.dish.pk}/'), 'Пока нет оценок')

		self.client.logout()
		self.assertNotContains(self.client.get(f'/dish/{self.dish.pk}/'), 'Отличное блюдо')

	def test_approved_reviews_are_averaged_on_detail_and_menu(self):
		second_user = User.objects.create_user(username='another', password='SafePassword_726!')
		Review.objects.create(dish=self.dish, user=self.user, rating=5, comment='Прекрасно', is_approved=True)
		Review.objects.create(dish=self.dish, user=second_user, rating=3, comment='Хорошо', is_approved=True)

		self.assertContains(self.client.get(f'/dish/{self.dish.pk}/'), '4,0')
		self.assertContains(self.client.get('/'), '4,0')

	def test_non_staff_users_cannot_open_admin_review_management(self):
		self.client.force_login(self.user)

		response = self.client.get('/admin/main/review/')

		self.assertEqual(response.status_code, 302)
		self.assertIn('/admin/login/', response.url)
		self.assertNotContains(self.client.get('/'), 'Управление')

	def test_staff_admin_can_open_review_moderation(self):
		admin_user = User.objects.create_superuser(
			username='moderator',
			email='moderator@example.com',
			password='SafePassword_726!',
		)
		self.client.force_login(admin_user)

		self.assertEqual(self.client.get('/admin/main/review/').status_code, 200)
		self.assertContains(self.client.get('/'), 'Управление')
