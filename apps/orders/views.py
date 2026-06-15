from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Order, OrderItem
from .cart import Cart
from menu.models import Meal
from django.urls import reverse_lazy

class CartAddView(View):
    def post(self, request, meal_id):
        cart = Cart(request)
        meal = get_object_or_404(Meal, id=meal_id)
        quantity = int(request.POST.get('quantity', 1))
        cart.add(meal=meal, quantity=quantity)
        return redirect('orders:cart_detail')

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

class CheckoutView(View):
    def get(self, request):
        cart = Cart(request)
        if len(cart) == 0:
            return redirect('menu:menu_list')
        return render(request, 'orders/checkout.html', {'cart': cart})

    def post(self, request):
        cart = Cart(request)
        if len(cart) == 0:
            return redirect('menu:menu_list')
        
        # Delivery charge is discussed with admin later, initially 0
        delivery_charge = 0
        
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=request.POST.get('full_name'),
            email=request.POST.get('email'),
            phone_number=request.POST.get('phone_number'),
            address=request.POST.get('address'),
            delivery_charge=delivery_charge,
            packaging_fee=cart.get_packaging_fee(),
            total_price=cart.get_grand_total(),
            payment_method=request.POST.get('payment_method', 'cod')
        )
        
        for item in cart:
            OrderItem.objects.create(
                order=order,
                meal=item['meal'],
                price=item['price'],
                quantity=item['quantity']
            )
        
        cart.clear()

        try:
            from django.core.mail import send_mail
            subject = f"New Order #{order.id} from {order.full_name}"
            message = f"A new order has been placed.\n\nOrder ID: {order.id}\nCustomer: {order.full_name}\nEmail: {order.email}\nPhone: {order.phone_number}\nAddress: {order.address}\nTotal: {order.total_price} FCFA\nPayment Method: {order.payment_method}\n\nPlease check the admin panel for details."
            
            send_mail(
                subject=subject,
                message=message,
                from_email='noreply@cakeprincess.com',
                recipient_list=['orders@cakeprincess.com'],
                fail_silently=True,
            )
        except Exception:
            pass

        return render(request, 'orders/order_created.html', {'order': order})
