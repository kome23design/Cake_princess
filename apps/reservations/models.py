from django.db import models
from django.conf import settings

class Reservation(models.Model):
    RESERVATION_TYPE_CHOICES = (
        ('table', 'Table Reservation'),
        ('birthday', 'Birthday Surprise'),
        ('engagement', 'Engagement Surprise'),
        ('event', 'General Event'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservations', null=True, blank=True)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    reservation_type = models.CharField(max_length=20, choices=RESERVATION_TYPE_CHOICES, default='table')
    date = models.DateField()
    time = models.TimeField()
    guest_count = models.PositiveIntegerField(default=1)
    special_requests = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date', '-time')

    def __str__(self):
        return f"{self.reservation_type} for {self.full_name} on {self.date}"
