from django import forms
from .models import Reservation
from pages.models import Branch

class ReservationForm(forms.ModelForm):
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.filter(is_active=True),
        required=True,
        empty_label="-- Select Branch --",
        widget=forms.Select(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-gold-500 focus:border-transparent font-medium text-charcoal'})
    )

    class Meta:
        model = Reservation
        fields = ['branch', 'full_name', 'email', 'phone_number', 'reservation_type', 'date', 'time', 'guest_count', 'special_requests']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'guest_count': forms.NumberInput(attrs={'type': 'number', 'min': '1'}),
        }

