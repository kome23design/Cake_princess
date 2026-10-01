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

from django.utils.html import format_html
import urllib.parse

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'phone_number', 'status', 'payment_method', 'total_price', 'is_paid', 'points_awarded', 'whatsapp_notification']
    list_filter = ['status', 'is_paid', 'points_awarded', 'payment_method', 'created_at']
    list_editable = ['status', 'is_paid']
    inlines = [OrderItemInline]
    search_fields = ['full_name', 'email', 'phone_number']

    def whatsapp_notification(self, obj):
        if obj.is_paid and obj.phone_number:
            message = f"Hello {obj.full_name}! 👑\n\nYour order #{obj.id} has been confirmed as paid.\n"
            if obj.points_awarded:
                message += f"\nYou have been rewarded with loyalty points for this purchase! Check your profile to see your total points.\n"
            message += f"\nThank you for choosing Cake Princess!"
            
            encoded_message = urllib.parse.quote(message)
            phone = str(obj.phone_number).replace('+', '').replace(' ', '')
            # Assuming Cameroon code if length suggests local number without country code
            if len(phone) == 9 and phone.startswith('6'):
                phone = f"237{phone}"
            
            url = f"https://wa.me/{phone}?text={encoded_message}"
            return format_html('<a href="{}" target="_blank" style="background-color: #25D366; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold;">Send on WhatsApp</a>', url)
        return "-"
    whatsapp_notification.short_description = 'Notify User'
