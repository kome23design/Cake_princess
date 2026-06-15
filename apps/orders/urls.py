from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('cart/', views.CartDetailView.as_view(), name='cart_detail'),
    path('cart/add/<int:meal_id>/', views.CartAddView.as_view(), name='cart_add'),
    path('cart/remove/<int:meal_id>/', views.CartRemoveView.as_view(), name='cart_remove'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('history/', views.OrderHistoryView.as_view(), name='order_history'),
]
