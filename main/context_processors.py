from .cart import Cart


def cart_summary(request):
    return {'cart_item_count': len(Cart(request))}
