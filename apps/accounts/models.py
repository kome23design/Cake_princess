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

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True, default='Yaounde')
    birth_date = models.DateField(null=True, blank=True)
    reward_points = models.PositiveIntegerField(default=0)
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
