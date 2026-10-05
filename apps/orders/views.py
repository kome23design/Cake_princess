from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Order, OrderItem, RewardSetting
from .cart import Cart
from menu.models import Meal
from django.urls import reverse_lazy

class OrderSuccessView(View):
    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        # Check permissions if necessary, but since it's just a success page, it's fine.
        import urllib.parse
        
        # We need the order_items_text for the whatsapp message, or we can just pass the order.
        # Actually, whatsapp_url might not be strictly needed on the success page if we already opened it,
        # but we can provide it for the "Track on WhatsApp" button.
        order_items_text = "\n".join([f"- {item.quantity}x {item.meal.name}" for item in order.items.all()])
        branch_info = f"📍 *Branch:* {order.branch_name or (order.branch.name if order.branch else 'Not specified')}\n" if (order.branch or order.branch_name) else ""
        points_info = f"💎 *Points Redeemed:* {order.points_redeemed} pts (Saved {order.discount_amount} FCFA with Reward Points!)\n" if (order.points_redeemed and order.points_redeemed > 0) else ""
        whatsapp_message = (
            f"Hello Cake Princess! 👑\n\n"
            f"I have just placed an order on your website.\n"
            f"🛍️ *Order ID:* #{order.id}\n"
            f"{branch_info}"
            f"📦 *Items:*\n{order_items_text}\n"
            f"👤 *Name:* {order.full_name}\n"
            f"📍 *Address:* {order.address}\n"
            f"{points_info}"
            f"💰 *Total To Pay:* {order.total_price} FCFA\n\n"
            f"Please confirm my order."
        )
        admin_phone = "237621643169"
        whatsapp_url = f"https://wa.me/{admin_phone}?text={urllib.parse.quote(whatsapp_message)}"
        
        return render(request, 'orders/order_created.html', {
            'order': order,
            'whatsapp_url': whatsapp_url
        })

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

def _resolve_order_branch(request):
    """Determine the active branch for an order or cart view."""
    from pages.models import Branch
    branch_id = request.POST.get('branch_id') if request.method == 'POST' else None
    branch = None
    if branch_id:
        try:
            branch = Branch.objects.filter(id=int(branch_id), is_active=True).first()
        except (ValueError, TypeError):
            branch = None
    if not branch:
        slug = request.session.get('selected_branch_slug') or request.COOKIES.get('selected_branch_slug')
        bid = request.session.get('selected_branch_id') or request.COOKIES.get('selected_branch_id')
        if slug:
            branch = Branch.objects.filter(slug=slug, is_active=True).first()
        elif bid:
            try:
                branch = Branch.objects.filter(id=int(bid), is_active=True).first()
            except (ValueError, TypeError):
                branch = None
    if not branch:
        branch = Branch.objects.filter(is_default=True, is_active=True).first() or Branch.objects.filter(is_active=True).first()
    return branch


def _get_reward_setting(branch=None):
    """Retrieve RewardSetting for a branch, with fallback to global setting."""
    if branch:
        setting = RewardSetting.objects.filter(branch=branch).first()
        if setting:
            return setting
    return RewardSetting.objects.filter(branch__isnull=True).first() or RewardSetting.objects.first()


def _get_reward_context(request, cart):
    """Helper: compute points-redeem discount and build context extras."""
    from django.utils import timezone

    branch = _resolve_order_branch(request)
    setting = _get_reward_setting(branch)
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

    if request.user.is_authenticated:
        if branch and hasattr(request.user, 'get_branch_points'):
            record = request.user.get_branch_reward_record(branch)
            if record and setting and setting.points_expiry_days:
                points_expired = record.check_and_expire_points(setting.points_expiry_days)
                if not points_expired and record.points_earned_at and setting.points_expiry_days:
                    expiry_date = record.points_earned_at + timezone.timedelta(days=setting.points_expiry_days)
            user_points = request.user.get_branch_points(branch)
        elif hasattr(request.user, 'profile'):
            profile = request.user.profile
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

        # Branch resolution
        branch = _resolve_order_branch(request)
        branch_name = branch.name if branch else 'Main'

        # --- Points redemption ---
        discount_amount = 0
        redeemed_points = 0
        setting = _get_reward_setting(branch)
        if request.user.is_authenticated and setting:
            if branch and hasattr(request.user, 'get_branch_points'):
                user_available_pts = request.user.get_branch_points(branch)
            elif hasattr(request.user, 'profile'):
                user_available_pts = request.user.profile.reward_points
            else:
                user_available_pts = 0

            pts_requested = int(request.session.get('redeem_points', 0))
            pts_allowed = min(pts_requested, user_available_pts)
            if pts_allowed > 0:
                discount_amount = pts_allowed * setting.points_value_in_fcfa
                if discount_amount > grand_total:
                    discount_amount = int(grand_total)
                redeemed_points = pts_allowed
                # Deduct points immediately from branch reward balance
                if branch and hasattr(request.user, 'deduct_branch_points'):
                    request.user.deduct_branch_points(branch, redeemed_points)
                if hasattr(request.user, 'profile') and request.user.profile.reward_points >= redeemed_points:
                    request.user.profile.reward_points -= redeemed_points
                    request.user.profile.save()

        total_price = int(grand_total) - discount_amount

        # Automatic payment method when user redeems points (only visible to admin)
        selected_payment = request.POST.get('payment_method', 'cod')
        if redeemed_points > 0:
            final_payment_method = 'points_redeemed'
            is_order_paid = (total_price <= 0)
        else:
            final_payment_method = selected_payment
            is_order_paid = False

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            branch=branch,
            branch_name=branch_name,
            full_name=request.POST.get('full_name'),
            email=request.POST.get('email'),
            phone_number=request.POST.get('phone_number'),
            address=request.POST.get('address'),
            delivery_charge=delivery_charge,
            packaging_fee=cart.get_packaging_fee(),
            total_price=total_price,
            discount_amount=discount_amount,
            points_redeemed=redeemed_points,
            payment_method=final_payment_method,
            is_paid=is_order_paid,
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
            subject = f"New Order #{order.id} from {order.full_name} [{branch_name}]"
            message = (
                f"A new order has been placed.\n\n"
                f"Order ID: {order.id}\n"
                f"Branch: {branch_name}\n"
                f"Customer: {order.full_name}\n"
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
        points_info = f"💎 *Points Redeemed:* {order.points_redeemed} pts (Saved {order.discount_amount} FCFA with Reward Points!)\n" if (order.points_redeemed and order.points_redeemed > 0) else ""
        whatsapp_message = (
            f"Hello Cake Princess! 👑\n\n"
            f"I have just placed an order on your website.\n"
            f"🛍️ *Order ID:* #{order.id}\n"
            f"📍 *Branch:* {branch_name}\n"
            f"📦 *Items:*\n{order_items_text}\n"
            f"👤 *Name:* {order.full_name}\n"
            f"📍 *Address:* {order.address}\n"
            f"{points_info}"
            f"💰 *Total To Pay:* {order.total_price} FCFA\n\n"
            f"Please confirm my order."
        )
        admin_phone = "237621643169"
        encoded_message = urllib.parse.quote(whatsapp_message)
        whatsapp_url = f"https://wa.me/{admin_phone}?text={encoded_message}"

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            from django.http import JsonResponse
            from django.urls import reverse
            success_url = reverse('orders:order_success', args=[order.id])
            return JsonResponse({
                'whatsapp_url': whatsapp_url,
                'success_url': success_url
            })

        return render(request, 'orders/order_created.html', {
            'order': order,
            'whatsapp_url': whatsapp_url
        })
