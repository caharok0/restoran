from decimal import Decimal, InvalidOperation

from .models import Dish


class Cart:
    SESSION_KEY = 'cart'
    MAX_QUANTITY = 99

    def __init__(self, request):
        self.session = request.session
        self.cart = self.session.setdefault(self.SESSION_KEY, {})

    def add(self, dish, quantity=1, update_quantity=False):
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            raise ValueError('Кількість має бути цілим числом.')

        dish_id = str(dish.pk)
        if not update_quantity:
            quantity += int(self.cart.get(dish_id, 0))

        if quantity < 1 or quantity > self.MAX_QUANTITY:
            raise ValueError(f'Кількість має бути від 1 до {self.MAX_QUANTITY}.')

        self.cart[dish_id] = quantity
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
        dishes = Dish.objects.in_bulk(self.cart.keys())
        items = []
        changed = False

        for dish_id in list(self.cart):
            dish = dishes.get(int(dish_id))
            if dish is None:
                self.cart.pop(dish_id, None)
                changed = True
                continue

            try:
                quantity = int(self.cart[dish_id])
                price = Decimal(dish.price)
            except (TypeError, ValueError, InvalidOperation):
                self.cart.pop(dish_id, None)
                changed = True
                continue

            if quantity < 1 or quantity > self.MAX_QUANTITY:
                self.cart.pop(dish_id, None)
                changed = True
                continue

            items.append({
                'dish': dish,
                'quantity': quantity,
                'price': price,
                'total_price': price * quantity,
            })

        if changed:
            self.save()
        return iter(items)

    def __len__(self):
        return sum(item['quantity'] for item in self)

    @property
    def total_price(self):
        return sum((item['total_price'] for item in self), Decimal('0.00'))
