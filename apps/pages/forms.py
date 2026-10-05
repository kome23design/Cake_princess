from django import forms
from .models import TrainingApplication, Branch

class TrainingApplicationForm(forms.ModelForm):
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.filter(is_active=True),
        required=True,
        empty_label="-- Select Training Branch --",
        widget=forms.Select(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-gold-500 focus:border-transparent font-medium text-charcoal'})
    )

    class Meta:
        model = TrainingApplication
        fields = ['branch', 'name', 'email', 'phone', 'course_level', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-gold-500 focus:border-transparent', 'placeholder': 'Your Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-gold-500 focus:border-transparent', 'placeholder': 'Your Email Address'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-gold-500 focus:border-transparent', 'placeholder': 'Your Phone Number'}),
            'course_level': forms.Select(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-gold-500 focus:border-transparent font-medium text-charcoal'}),
            'message': forms.Textarea(attrs={'class': 'w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-gold-500 focus:border-transparent', 'rows': 4, 'placeholder': 'Tell us why you want to join and any prior experience...'}),
        }

