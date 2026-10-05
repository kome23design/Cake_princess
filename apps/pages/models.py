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

class Branch(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Branch name, e.g. Jouvence, Bastos")
    slug = models.SlugField(max_length=100, unique=True)
    tagline = models.CharField(max_length=200, blank=True, help_text="e.g. Fine Dining & Pastry Palace")
    hero_title = models.CharField(max_length=200, blank=True, help_text="Custom hero heading for this branch (leave blank to use default)")
    hero_subtitle = models.TextField(blank=True, help_text="Custom hero subheading for this branch (leave blank to use default)")
    address = models.CharField(max_length=255, default='Yaounde, Cameroon')
    phone = models.CharField(max_length=50, default='+237 621 643 169')
    email = models.EmailField(blank=True, default='hello@cakeprincess.com')
    opening_hours = models.CharField(max_length=150, default='Every day from 11:00 AM')
    map_embed_url = models.TextField(blank=True, help_text="Google Maps embed iframe src or URL")
    image = models.ImageField(upload_to='branches/', blank=True, null=True, help_text="Representative photo of this branch")
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False, help_text="Set as default branch when user hasn't selected one")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Branch"
        verbose_name_plural = "Branches"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_default:
            Branch.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class BranchHeroImage(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='hero_images')
    image = models.ImageField(upload_to='branches/heroes/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Branch Hero Image"
        verbose_name_plural = "Branch Hero Images"

    def __str__(self):
        return f"{self.branch.name} - Image #{self.id}"


class BranchNavLink(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='nav_links')
    title = models.CharField(max_length=100)
    url = models.CharField(max_length=255, help_text="URL path, e.g. /menu/, /services/, /reservations/")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Branch Nav Link"
        verbose_name_plural = "Branch Nav Links"

    def __str__(self):
        return f"{self.branch.name} - {self.title}"


class Service(models.Model):
    ICON_CHOICES = [
        ('cake', 'Cake & Pastry (Birthday / Celebration)'),
        ('truck', 'Fast Delivery'),
        ('sparkles', 'Surprise & Decor Planning'),
        ('calendar', 'Event & Table Reservations'),
        ('gift', 'Gift Hampers & Corporate Packages'),
        ('academic', 'Culinary & Baking Training'),
        ('cutlery', 'Bespoke Catering & Buffet'),
    ]
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    short_description = models.CharField(max_length=255, help_text="Short teaser for cards")
    description = models.TextField(help_text="Detailed description of the service")
    icon = models.CharField(max_length=50, choices=ICON_CHOICES, default='cake')
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    price_starting_at = models.CharField(max_length=100, blank=True, help_text="e.g. From 15,000 FCFA or Custom Quote")
    features = models.TextField(blank=True, help_text="List key features, one item per line")
    branches = models.ManyToManyField(Branch, related_name='services', blank=True, help_text="Branches offering this service. Leave blank to offer across ALL branches.")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'title']
        verbose_name = "Service Offered"
        verbose_name_plural = "Services Offered"

    def __str__(self):
        return self.title

    def get_features_list(self):
        if not self.features:
            return []
        return [f.strip() for f in self.features.splitlines() if f.strip()]


class TrainingExplanation(models.Model):
    title = models.CharField(max_length=200, default='Professional Baking & Pastry Arts Program')
    subtitle = models.CharField(max_length=300, default='Empowering the next generation of master bakers, pastry artists, and culinary entrepreneurs in Cameroon.')
    overview = models.TextField(help_text="Full in-depth explanation of the training program and training experience.")
    curriculum = models.TextField(help_text="Course modules breakdown. Format: one module or section per line.")
    duration_info = models.CharField(max_length=200, default='3 Months (Intensive) / 6 Months (Masterclass)')
    schedule_info = models.CharField(max_length=200, default='Morning Sessions (9:00 AM - 1:00 PM) & Weekend Batches')
    certification_info = models.CharField(max_length=200, default='Cake Princess Diplôme de Pâtisserie & Recommendation')
    kit_included = models.CharField(max_length=200, default='Complete Professional Starter Pastry Kit & Branded Apron')
    eligibility_info = models.CharField(max_length=200, default='Open to beginners, culinary lovers, and professional upskillers')
    faq_text = models.TextField(blank=True, help_text="Frequently asked questions, formatted with Q: and A: or lines")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Training Page Explanation"
        verbose_name_plural = "Training Page Explanations"

    def __str__(self):
        return self.title

    def get_curriculum_list(self):
        if not self.curriculum:
            return []
        return [line.strip() for line in self.curriculum.splitlines() if line.strip()]

    def get_faq_list(self):
        if not self.faq_text:
            return []
        lines = [line.strip() for line in self.faq_text.splitlines() if line.strip()]
        faqs = []
        current_q = None
        current_a = []
        for line in lines:
            if line.startswith('Q:') or line.startswith('**Q:'):
                if current_q:
                    faqs.append({'q': current_q, 'a': ' '.join(current_a)})
                current_q = line.replace('Q:', '').replace('**Q:', '').replace('**', '').strip()
                current_a = []
            elif line.startswith('A:') or line.startswith('**A:'):
                current_a.append(line.replace('A:', '').replace('**A:', '').replace('**', '').strip())
            else:
                if current_q:
                    current_a.append(line)
        if current_q:
            faqs.append({'q': current_q, 'a': ' '.join(current_a)})
        return faqs


class TrainingApplication(models.Model):
    COURSE_LEVELS = [
        ('beginner', 'Beginner Level'),
        ('intermediate', 'Intermediate Level'),
        ('advanced', 'Advanced Masterclass'),
    ]
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='training_applications', help_text="Branch where applicant wants to train")
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    course_level = models.CharField(max_length=20, choices=COURSE_LEVELS, default='beginner')
    message = models.TextField(blank=True, help_text="Why do you want to join this training or any prior experience?")
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-applied_at']

    def __str__(self):
        branch_str = f" [{self.branch.name}]" if self.branch else ""
        return f"{self.name} - {self.get_course_level_display()}{branch_str}"

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

class MarqueeSetting(models.Model):
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='marquee_settings',
        help_text="Branch for this marquee announcement. Leave blank to display across all branches."
    )
    text = models.CharField(max_length=500, help_text="Text to display in the marquee bar")
    active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Marquee Setting"
        verbose_name_plural = "Marquee Settings"
        
    def __str__(self):
        branch_str = f"[{self.branch.name}] " if self.branch else "[All Branches] "
        return f"{branch_str}{self.text[:50]}"

