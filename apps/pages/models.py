from django.db import models
from django.urls import reverse

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    image = models.ImageField(upload_to='blog/', blank=True, null=True)
    author = models.CharField(max_length=100, default='Cake Princess')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('pages:blog_detail', kwargs={'slug': self.slug})

class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    image = models.ImageField(upload_to='team/')
    bio = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} - {self.role}"

class TrainingApplication(models.Model):
    COURSE_LEVELS = [
        ('beginner', 'Beginner Level'),
        ('intermediate', 'Intermediate Level'),
        ('advanced', 'Advanced Masterclass'),
    ]
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    course_level = models.CharField(max_length=20, choices=COURSE_LEVELS, default='beginner')
    message = models.TextField(blank=True, help_text="Why do you want to join this training or any prior experience?")
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.name} - {self.get_course_level_display()}"

class GraduationEventImage(models.Model):
    image = models.ImageField(upload_to='training/graduations/')
    caption = models.CharField(max_length=200, blank=True)
    event_date = models.DateField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-event_date', '-uploaded_at']

    def __str__(self):
        if self.caption:
            return self.caption
        return f"Graduation Image {self.id}"
