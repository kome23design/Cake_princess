from django import forms
from .models import Reservation

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['full_name', 'email', 'phone_number', 'reservation_type', 'date', 'time', 'guest_count', 'special_requests']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'guest_count': forms.NumberInput(attrs={'type': 'number', 'min': '1'}),
        }
