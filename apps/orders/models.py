from django.db import models
from django.conf import settings
from menu.models import Meal
from django.utils import timezone

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    discount = models.PositiveIntegerField()
    is_percentage = models.BooleanField(default=True, help_text="If checked, discount is a percentage. Otherwise, it's a fixed amount (FCFA).")
    points_required = models.PositiveIntegerField(default=0, help_text="Number of reward points required to use this coupon.")
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

    def is_valid(self):
        now = timezone.now()
        return self.active and self.valid_from <= now <= self.valid_to

class RewardSetting(models.Model):
    branch = models.OneToOneField(
        'pages.Branch',
        on_delete=models.CASCADE,
        related_name='reward_setting',
        null=True,
        blank=True,
        help_text="Branch for this reward setting. Leave blank for default / global setting."
    )
    amount_spent_per_point = models.PositiveIntegerField(default=100, help_text="Amount in FCFA spent to earn 1 point")
    points_earned = models.PositiveIntegerField(default=1, help_text="Points earned per threshold amount")
    points_value_in_fcfa = models.PositiveIntegerField(default=10, help_text="FCFA value of 1 redeemed point (e.g. 1 point = 10 FCFA off)")
    min_redeemable_points = models.PositiveIntegerField(default=50, help_text="Minimum points a customer must have before they can redeem any")
    points_expiry_days = models.PositiveIntegerField(
        default=365,
        help_text="Number of days points are valid from the date the user first earned them. Set to 0 for no expiry."
    )

    def __str__(self):
        branch_name = self.branch.name if self.branch else "Global Default"
        return (
            f"[{branch_name}] {self.points_earned} pts per {self.amount_spent_per_point} FCFA | "
            f"1 pt = {self.points_value_in_fcfa} FCFA | "
            f"Min redeem: {self.min_redeemable_points} pts | "
            f"Expiry: {self.points_expiry_days} days"
        )

    class Meta:
        verbose_name = "Reward Setting"
        verbose_name_plural = "Reward Settings"

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('on_delivery', 'On Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_CHOICES = (
        ('cod', 'Cash on Delivery'),
        ('momo', 'Mobile Money'),
        ('points_redeemed', 'Paid with Redeemed Points'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    branch = models.ForeignKey('pages.Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders', help_text="Branch from which the order was placed")
    branch_name = models.CharField(max_length=100, blank=True, help_text="Branch name snapshot")
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100, default='Yaounde')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, choices=PAYMENT_CHOICES, default='cod')
    total_price = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    packaging_fee = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    is_paid = models.BooleanField(default=False)
    coupon = models.ForeignKey(Coupon, related_name='orders', null=True, blank=True, on_delete=models.SET_NULL)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    points_redeemed = models.PositiveIntegerField(default=0, help_text="Reward points redeemed by customer on this order")
    points_awarded = models.BooleanField(default=False)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f"Order {self.id}"

    def get_total_cost(self):
        return self.total_price + self.delivery_charge + self.packaging_fee - self.discount_amount

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.user and not self.points_awarded:
            if self.status == 'delivered' or self.is_paid:
                try:
                    from django.utils import timezone
                    setting = None
                    if self.branch:
                        setting = RewardSetting.objects.filter(branch=self.branch).first()
                    if not setting:
                        setting = RewardSetting.objects.filter(branch__isnull=True).first() or RewardSetting.objects.first()
                    if setting and setting.amount_spent_per_point > 0:
                        points_to_add = int((self.total_price / setting.amount_spent_per_point) * setting.points_earned)
                        if points_to_add > 0:
                            # Award to specific branch reward balance
                            if self.branch and hasattr(self.user, 'add_branch_points'):
                                self.user.add_branch_points(self.branch, points_to_add)
                            if hasattr(self.user, 'profile'):
                                profile = self.user.profile
                                # Set points_earned_at only on first-ever points
                                if profile.reward_points == 0 or profile.points_earned_at is None:
                                    profile.points_earned_at = timezone.now()
                                profile.reward_points += points_to_add
                                profile.save()
                            self.points_awarded = True
                            Order.objects.filter(pk=self.pk).update(points_awarded=True)
                except Exception:
                    pass

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    meal = models.ForeignKey(Meal, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=0)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        return self.price * self.quantity

class DailyPaidOrder(Order):
    class Meta:
        proxy = True
        verbose_name = "Daily Paid Order Report"
        verbose_name_plural = "Daily Paid Orders Report"

