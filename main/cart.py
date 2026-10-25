from decimal import Decimal, InvalidOperation

from .models import Dish


class Cart:
    """A session-backed shopping cart keyed by dish primary key."""

    SESSION_KEY = 'cart'
    MAX_QUANTITY = 99

    def __init__(self, request):
        self.session = request.session
        self.cart = self.session.setdefault(self.SESSION_KEY, {})

    def add(self, dish, quantity=1, update_quantity=False):
        try:
            quantity = int(quantity)
        except (TypeError, ValueError) as exc:
            raise ValueError('Кількість має бути цілим числом.') from exc

        if quantity < 1 or quantity > self.MAX_QUANTITY:
            raise ValueError(f'Кількість має бути від 1 до {self.MAX_QUANTITY}.')

        dish_id = str(dish.pk)
        current_quantity = int(self.cart.get(dish_id, 0))
        self.cart[dish_id] = quantity if update_quantity else current_quantity + quantity
        self.save()

    def remove(self, dish):
        self.cart.pop(str(dish.pk), None)
        self.save()

    def save(self):
        self.session[self.SESSION_KEY] = self.cart
        self.session.modified = True

    def clear(self):
        self.session.pop(self.SESSION_KEY, None)
        self.cart = {}
        self.session.modified = True

    def __iter__(self):
        dish_ids = list(self.cart.keys())
        dishes = Dish.objects.filter(pk__in=dish_ids).in_bulk()
        items = []

        for dish_id in dish_ids:
            dish = dishes.get(int(dish_id))
            if dish is None:
                self.cart.pop(dish_id, None)
                continue
            try:
                quantity = int(self.cart[dish_id])
                price = Decimal(dish.price)
            except (TypeError, ValueError, InvalidOperation):
                self.cart.pop(dish_id, None)
                continue
            if quantity < 1 or quantity > self.MAX_QUANTITY:
                self.cart.pop(dish_id, None)
                continue

            items.append({
                'dish': dish,
                'quantity': quantity,
                'price': price,
                'total_price': price * quantity,
            })

        if len(items) != len(dish_ids):
            self.save()
        return iter(items)

    def __len__(self):
        return sum(item['quantity'] for item in self)

    @property
    def total_price(self):
        return sum((item['total_price'] for item in self), Decimal('0.00'))
