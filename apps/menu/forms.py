from django import forms
from .models import MadeOnCommandInquiry

class MadeOnCommandInquiryForm(forms.ModelForm):
    class Meta:
        model = MadeOnCommandInquiry
        fields = ['name', 'email', 'phone', 'event_date', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-gold-500 focus:border-transparent', 'placeholder': 'Your Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-gold-500 focus:border-transparent', 'placeholder': 'Your Email Address'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-gold-500 focus:border-transparent', 'placeholder': 'Your Phone Number'}),
            'event_date': forms.DateInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-gold-500 focus:border-transparent', 'type': 'date'}),
            'message': forms.Textarea(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-gold-500 focus:border-transparent', 'rows': 4, 'placeholder': 'Please tell us more about your request...'}),
        }
