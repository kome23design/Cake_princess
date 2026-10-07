from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    def _create_user(self, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)
    phone_number = PhoneNumberField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    def get_branch_points(self, branch):
        if not branch:
            return 0
        record = self.branch_rewards.filter(branch=branch).first()
        return record.points if record else 0

    def get_branch_reward_record(self, branch):
        if not branch:
            return None
        return self.branch_rewards.filter(branch=branch).first()

    def add_branch_points(self, branch, points_to_add):
        if not branch or points_to_add <= 0:
            return None
        from django.utils import timezone
        record, created = UserBranchReward.objects.get_or_create(
            user=self,
            branch=branch,
            defaults={'points': 0}
        )
        if record.points == 0 or record.points_earned_at is None:
            record.points_earned_at = timezone.now()
        record.points += points_to_add
        record.save()
        return record

    def deduct_branch_points(self, branch, points_to_deduct):
        if not branch or points_to_deduct <= 0:
            return None
        record = self.branch_rewards.filter(branch=branch).first()
        if record and record.points >= points_to_deduct:
            record.points -= points_to_deduct
            record.save()
            return record
        return None

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True, default='Yaounde')
    birth_date = models.DateField(null=True, blank=True)
    reward_points = models.PositiveIntegerField(default=0, help_text="Total legacy points across all branches")
    points_earned_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Timestamp of when the user first earned reward points. Used to calculate expiry."
    )

    def __str__(self):
        return f"{self.user.email}'s Profile"

    def check_and_expire_points(self, expiry_days):
        """Expire points if the expiry window has passed. Returns True if expired."""
        from django.utils import timezone
        if self.reward_points > 0 and self.points_earned_at and expiry_days:
            expiry_date = self.points_earned_at + timezone.timedelta(days=expiry_days)
            if timezone.now() > expiry_date:
                self.reward_points = 0
                self.points_earned_at = None
                self.save(update_fields=['reward_points', 'points_earned_at'])
                return True
        return False



class UserBranchReward(models.Model):
    """Tracks reward points for a specific user within a specific branch."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='branch_rewards')
    branch = models.ForeignKey('pages.Branch', on_delete=models.CASCADE, related_name='user_rewards')
    points = models.PositiveIntegerField(default=0, help_text="Points earned at this branch")
    points_earned_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Timestamp of when the user first earned reward points at this branch."
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'branch')
        verbose_name = "User Branch Reward"
        verbose_name_plural = "User Branch Rewards"

    def __str__(self):
        return f"{self.user.email} - {self.branch.name}: {self.points} pts"

    def check_and_expire_points(self, expiry_days):
        from django.utils import timezone
        if self.points > 0 and self.points_earned_at and expiry_days:
            expiry_date = self.points_earned_at + timezone.timedelta(days=expiry_days)
            if timezone.now() > expiry_date:
                self.points = 0
                self.points_earned_at = None
                self.save(update_fields=['points', 'points_earned_at'])
                return True
        return False



class PushSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions')
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=200)
    auth = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.endpoint[:30]}..."
