from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Order, OrderItem, RewardSetting
from .cart import Cart
from menu.models import Meal
from django.urls import reverse_lazy

class CartAddView(View):
    def post(self, request, meal_id):
        from django.http import JsonResponse
        cart = Cart(request)
        meal = get_object_or_404(Meal, id=meal_id)
        quantity = int(request.POST.get('quantity', 1))
        cart.add(meal=meal, quantity=quantity)
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'cart_total': len(cart)})
            
        return redirect(request.META.get('HTTP_REFERER', 'menu:menu_list'))

class CartRemoveView(View):
    def post(self, request, meal_id):
        cart = Cart(request)
        meal = get_object_or_404(Meal, id=meal_id)
        cart.remove(meal)
        return redirect('orders:cart_detail')

class CartDetailView(View):
    def get(self, request):
        cart = Cart(request)
        return render(request, 'orders/cart_detail.html', {'cart': cart})

class OrderHistoryView(ListView):
    model = Order
    template_name = 'orders/order_history.html'
    context_object_name = 'orders'

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Order.objects.filter(user=self.request.user)
        return Order.objects.none()

def _get_reward_context(request, cart):
    """Helper: compute points-redeem discount and build context extras."""
    from django.utils import timezone

    setting = RewardSetting.objects.first()
    user_points = 0
    points_to_redeem = 0
    points_discount = 0
    points_expired = False
    min_redeemable = 0
    point_value = 0
    expiry_date = None

    if setting:
        min_redeemable = setting.min_redeemable_points
        point_value = setting.points_value_in_fcfa

    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        profile = request.user.profile
        # Check and auto-expire points if window has passed
        if setting and setting.points_expiry_days:
            points_expired = profile.check_and_expire_points(setting.points_expiry_days)
            if not points_expired and profile.points_earned_at and setting.points_expiry_days:
                expiry_date = profile.points_earned_at + timezone.timedelta(days=setting.points_expiry_days)
        user_points = profile.reward_points

    # Points the user wants to redeem this session
    points_to_redeem = int(request.session.get('redeem_points', 0))
    can_redeem = user_points >= min_redeemable and not points_expired

    if points_to_redeem > 0 and can_redeem and setting:
        # Cap to user balance
        points_to_redeem = min(points_to_redeem, user_points)
        points_discount = points_to_redeem * point_value
        grand_total = cart.get_grand_total()
        if points_discount > grand_total:
            points_discount = int(grand_total)
    else:
        points_to_redeem = 0

    return {
        'setting': setting,
        'user_points': user_points,
        'points_to_redeem': points_to_redeem,
        'points_discount': points_discount,
        'min_redeemable': min_redeemable,
        'point_value': point_value,
        'points_expired': points_expired,
        'expiry_date': expiry_date,
        'can_redeem': can_redeem,
        'final_total': int(cart.get_grand_total()) - points_discount,
    }


class CheckoutView(View):
    def get(self, request):
        cart = Cart(request)
        if len(cart) == 0:
            return redirect('menu:menu_list')

        context = {'cart': cart}
        context.update(_get_reward_context(request, cart))
        return render(request, 'orders/checkout.html', context)

    def post(self, request):
        # Handle "Apply Points" button
        if 'apply_points' in request.POST:
            try:
                pts = int(request.POST.get('redeem_points', 0))
            except (ValueError, TypeError):
                pts = 0
            request.session['redeem_points'] = pts
            return redirect('orders:checkout')

        cart = Cart(request)
        if len(cart) == 0:
            return redirect('menu:menu_list')

        delivery_charge = 0
        grand_total = cart.get_grand_total()

        # --- Points redemption ---
        discount_amount = 0
        redeemed_points = 0
        setting = RewardSetting.objects.first()
        if request.user.is_authenticated and setting and hasattr(request.user, 'profile'):
            profile = request.user.profile
            pts_requested = int(request.session.get('redeem_points', 0))
            pts_allowed = min(pts_requested, profile.reward_points)
            if pts_allowed > 0:
                discount_amount = pts_allowed * setting.points_value_in_fcfa
                if discount_amount > grand_total:
                    discount_amount = int(grand_total)
                redeemed_points = pts_allowed
                # Deduct points immediately
                profile.reward_points -= redeemed_points
                profile.save()

        total_price = int(grand_total) - discount_amount

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=request.POST.get('full_name'),
            email=request.POST.get('email'),
            phone_number=request.POST.get('phone_number'),
            address=request.POST.get('address'),
            delivery_charge=delivery_charge,
            packaging_fee=cart.get_packaging_fee(),
            total_price=total_price,
            discount_amount=discount_amount,
            # coupon field left null — coupons commented out for now
            payment_method=request.POST.get('payment_method', 'cod')
        )

        order_items_list = []
        for item in cart:
            OrderItem.objects.create(
                order=order,
                meal=item['meal'],
                price=item['price'],
                quantity=item['quantity']
            )
            order_items_list.append(f"- {item['quantity']}x {item['meal'].name}")

        order_items_text = "\n".join(order_items_list)

        cart.clear()
        # Clear redeemed points from session
        if 'redeem_points' in request.session:
            del request.session['redeem_points']

        try:
            from django.core.mail import send_mail
            subject = f"New Order #{order.id} from {order.full_name}"
            message = (
                f"A new order has been placed.\n\n"
                f"Order ID: {order.id}\nCustomer: {order.full_name}\n"
                f"Email: {order.email}\nPhone: {order.phone_number}\n"
                f"Address: {order.address}\nTotal: {order.total_price} FCFA\n"
                f"Discount: {order.discount_amount} FCFA\n"
                f"Payment Method: {order.payment_method}\n\n"
                f"Please check the admin panel for details."
            )
            send_mail(
                subject=subject,
                message=message,
                from_email='noreply@cakeprincess.com',
                recipient_list=['orders@cakeprincess.com'],
                fail_silently=True,
            )
        except Exception:
            pass

        import urllib.parse
        whatsapp_message = (
            f"Hello Cake Princess! 👑\n\n"
            f"I have just placed an order on your website.\n"
            f"🛍️ *Order ID:* #{order.id}\n"
            f"📦 *Items:*\n{order_items_text}\n"
            f"👤 *Name:* {order.full_name}\n"
            f"📍 *Address:* {order.address}\n"
            f"💰 *Total:* {order.total_price} FCFA\n\n"
            f"Please confirm my order."
        )
        encoded_message = urllib.parse.quote(whatsapp_message)
        whatsapp_url = f"https://wa.me/237621643169?text={encoded_message}"

        return redirect(whatsapp_url)
