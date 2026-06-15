from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['meal']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'email', 'status', 'payment_method', 'total_price', 'is_paid', 'created_at']
    list_filter = ['status', 'is_paid', 'payment_method', 'created_at']
    list_editable = ['status', 'is_paid']
    inlines = [OrderItemInline]
    search_fields = ['full_name', 'email', 'phone_number']
