from pages.models import MarqueeSetting

def marquee_text(request):
    try:
        marquee = MarqueeSetting.objects.filter(active=True).first()
        return {
            'marquee_text': marquee.text if marquee else None
        }
    except Exception:
        return {'marquee_text': None}


def cart(request):
    """Inject the Cart object into every template so the navbar badge is always accurate."""
    try:
        from orders.cart import Cart
        return {'cart': Cart(request)}
    except Exception:
        return {'cart': None}
