from django.db import models
from django.conf import settings
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('menu:category_detail', kwargs={'slug': self.slug})

class Meal(models.Model):
    category = models.ForeignKey(Category, related_name='meals', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=0)  # Price in FCFA (no decimals usually)
    image = models.ImageField(upload_to='meals/', blank=True, null=True)
    DAYS_OF_WEEK = (
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    )
    available_days = models.CharField(max_length=20, default='0123456', help_text="Digits 0-6 representing Monday-Sunday")
    is_available = models.BooleanField(default=True)
    is_daily_special = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_available_today(self):
        import datetime
        today = str(datetime.datetime.now().weekday())
        return self.is_available and today in self.available_days

    def get_next_available_day(self):
        import datetime
        today = datetime.datetime.now().weekday()
        days_map = dict(self.DAYS_OF_WEEK)
        # Check from tomorrow onwards
        for i in range(1, 8):
            next_day = (today + i) % 7
            if str(next_day) in self.available_days:
                return days_map[str(next_day)]
        return None

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('menu:meal_detail', kwargs={'slug': self.slug})

class MealImage(models.Model):
    meal = models.ForeignKey(Meal, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='meals/gallery/')
    alt_text = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Image for {self.meal.name}"

class Review(models.Model):
    meal = models.ForeignKey(Meal, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        user_email = self.user.email if self.user else "Guest"
        return f"Review by {user_email} on {self.meal.name}"

class MadeOnCommandItem(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    image = models.ImageField(upload_to='custom_items/')
    category = models.ForeignKey(Category, related_name='custom_items', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('menu:custom_item_detail', kwargs={'slug': self.slug})

class MadeOnCommandInquiry(models.Model):
    item = models.ForeignKey(MadeOnCommandItem, related_name='inquiries', on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    event_date = models.DateField(null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Made on Command Inquiries'

    def __str__(self):
        return f"Inquiry from {self.name} for {self.item.title}"
