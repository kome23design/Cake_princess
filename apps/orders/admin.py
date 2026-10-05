from django.contrib import admin
from .models import Order, OrderItem, RewardSetting, DailyPaidOrder
from django.db.models import Sum

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['meal']

@admin.register(RewardSetting)
class RewardSettingAdmin(admin.ModelAdmin):
    list_display = ['branch', 'amount_spent_per_point', 'points_earned', 'points_value_in_fcfa', 'min_redeemable_points', 'points_expiry_days']
    list_filter = ['branch']

from django.utils.html import format_html
import urllib.parse

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'branch', 'phone_number', 'status', 'payment_method_badge', 'total_price', 'points_redeemed', 'discount_amount', 'is_paid', 'points_awarded', 'whatsapp_notification']
    list_filter = ['branch', 'status', 'is_paid', 'points_awarded', 'payment_method', 'created_at']
    list_editable = ['status', 'is_paid']
    inlines = [OrderItemInline]
    search_fields = ['full_name', 'email', 'phone_number', 'branch_name']
    exclude = ['coupon']
    readonly_fields = ['points_redeemed', 'discount_amount', 'points_awarded', 'created_at', 'updated_at']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        search_term = request.GET.get('q', '').strip()
        is_date_search = False
        
        if search_term:
            import datetime
            formats = ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']
            for fmt in formats:
                try:
                    datetime.datetime.strptime(search_term, fmt).date()
                    is_date_search = True
                    break
                except ValueError:
                    pass
                    
        has_date_filter = any(key.startswith('created_at') for key in request.GET.keys())
        if not is_date_search and not has_date_filter:
            from django.utils import timezone
            qs = qs.filter(created_at__date=timezone.now().date())
        return qs

    def get_search_results(self, request, queryset, search_term):
        search_term = search_term.strip()
        qs, use_distinct = super().get_search_results(request, queryset, search_term)
        
        if search_term:
            import datetime
            parsed_date = None
            formats = ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']
            for fmt in formats:
                try:
                    parsed_date = datetime.datetime.strptime(search_term, fmt).date()
                    break
                except ValueError:
                    pass
                    
            if parsed_date:
                date_qs = queryset.model.objects.filter(created_at__date=parsed_date)
                qs = qs | date_qs
                use_distinct = True
                
        return qs, use_distinct

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = Order.objects.get(pk=obj.pk)
            if obj.is_paid and not old_obj.is_paid:
                if obj.status == 'pending':
                    obj.status = 'confirmed'
        super().save_model(request, obj, form, change)

    def payment_method_badge(self, obj):
        if obj.payment_method == 'points_redeemed':
            return format_html(
                '<span class="badge badge-info" style="font-size: 11px; padding: 4px 8px;">'
                '?? Paid with Redeemed Points</span>'
            )
        return obj.get_payment_method_display()
    payment_method_badge.short_description = 'Payment Method'

    def whatsapp_notification(self, obj):
        if obj.is_paid and obj.phone_number:
            points_line = f"\nPoints Redeemed: {obj.points_redeemed} pts (-{obj.discount_amount} FCFA)\n" if obj.points_redeemed > 0 else ""
            message = f"Hello {obj.full_name}! ??\n\nYour order #{obj.id} has been confirmed as paid.\n{points_line}"
            if obj.points_awarded:
                message += f"\nYou have been rewarded with loyalty points for this purchase! Check your profile to see your total points.\n"
            message += f"\nThank you for choosing Cake Princess!"
            
            encoded_message = urllib.parse.quote(message)
            phone = str(obj.phone_number).replace('+', '').replace(' ', '')
            if len(phone) == 9 and phone.startswith('6'):
                phone = f"237{phone}"
            
            url = f"https://wa.me/{phone}?text={encoded_message}"
            return format_html('<a href="{}" target="_blank" style="background-color: #25D366; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold;">Send on WhatsApp</a>', url)
        return "-"
    whatsapp_notification.short_description = 'Notify User'


@admin.register(DailyPaidOrder)
class DailyPaidOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'branch', 'meals_list', 'total_price', 'points_awarded', 'points_redeemed', 'discount_amount', 'created_at']
    list_filter = ['branch', 'created_at']
    search_fields = ['full_name', 'email', 'phone_number', 'branch_name']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.filter(is_paid=True)
        if not any(key.startswith('created_at') for key in request.GET.keys()):
            from django.utils import timezone
            qs = qs.filter(created_at__date=timezone.now().date())
        return qs
        
    def meals_list(self, obj):
        items = obj.items.all()
        return ", ".join([f"{item.meal.name} (x{item.quantity})" for item in items])
    meals_list.short_description = "Meals"
    
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            qs = response.context_data["cl"].queryset
            
            total_price_sum = 0
            total_points_awarded = 0
            total_points_redeemed = 0
            total_discount = 0
            total_meals = 0
            
            from .models import RewardSetting
            settings_cache = {rs.branch_id: rs for rs in RewardSetting.objects.all()}
            default_setting = RewardSetting.objects.filter(branch__isnull=True).first() or RewardSetting.objects.first()
            
            for order in qs.prefetch_related('items', 'items__meal'):
                total_price_sum += order.total_price
                total_points_redeemed += order.points_redeemed
                total_discount += order.discount_amount
                total_meals += sum(item.quantity for item in order.items.all())
                
                if order.points_awarded:
                    setting = settings_cache.get(order.branch_id) or default_setting
                    if setting and setting.amount_spent_per_point > 0:
                        pts = int((order.total_price / setting.amount_spent_per_point) * setting.points_earned)
                        total_points_awarded += pts

            aggregates = {
                'total_price_sum': total_price_sum,
                'total_points_awarded': total_points_awarded,
                'total_points_redeemed': total_points_redeemed,
                'total_discount': total_discount,
            }
            
            extra = {
                "aggregates": aggregates,
                "total_meals": total_meals,
            }
            response.context_data.update(extra)
        except (AttributeError, KeyError):
            pass
        return response
