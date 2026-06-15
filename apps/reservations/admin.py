from django.contrib import admin
from .models import Reservation

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'reservation_type', 'date', 'time', 'guest_count', 'status', 'created_at']
    list_filter = ['status', 'reservation_type', 'date']
    list_editable = ['status']
    search_fields = ['full_name', 'email', 'phone_number']
    actions = ['approve_reservations']

    def approve_reservations(self, request, queryset):
        queryset.update(status='approved')
    approve_reservations.short_description = "Approve selected reservations"
