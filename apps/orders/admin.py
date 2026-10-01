from django.contrib import admin
from .models import Order, OrderItem, Coupon, RewardSetting

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['meal']

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'valid_from', 'valid_to', 'discount', 'is_percentage', 'points_required', 'active']
    list_filter = ['active', 'is_percentage', 'valid_from', 'valid_to']
    search_fields = ['code']

@admin.register(RewardSetting)
class RewardSettingAdmin(admin.ModelAdmin):
    list_display = ['amount_spent_per_point', 'points_earned', 'points_value_in_fcfa', 'min_redeemable_points', 'points_expiry_days']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'email', 'status', 'payment_method', 'total_price', 'discount_amount', 'is_paid', 'points_awarded', 'created_at']
    list_filter = ['status', 'is_paid', 'points_awarded', 'payment_method', 'created_at']
    list_editable = ['status', 'is_paid']
    inlines = [OrderItemInline]
    search_fields = ['full_name', 'email', 'phone_number']
