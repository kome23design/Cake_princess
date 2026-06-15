from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, DetailView, CreateView
from menu.models import Meal, Category, Review
from .models import BlogPost

class HomeView(TemplateView):
    template_name = 'pages/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['featured_meals'] = Meal.objects.filter(is_daily_special=True)[:6]
        context['reviews'] = Review.objects.filter(is_approved=True).order_by('-created_at')[:6]
        return context

class AboutView(TemplateView):
    template_name = 'pages/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import TeamMember
        context['team_members'] = TeamMember.objects.all()
        return context

from django.core.mail import send_mail
from django.shortcuts import redirect

class ContactView(TemplateView):
    template_name = 'pages/contact.html'

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name', 'Unknown')
        email = request.POST.get('email', 'No Email')
        subject = request.POST.get('subject', 'No Subject')
        message = request.POST.get('message', '')
        
        full_message = f"Message from {name} ({email}):\n\n{message}"
        
        try:
            send_mail(
                subject=f"Contact Form: {subject}",
                message=full_message,
                from_email='noreply@cakeprincess.com',
                recipient_list=['hello@cakeprincess.com'],
                fail_silently=True,
            )
        except Exception:
            pass
            
        return redirect('pages:contact')

class FAQView(TemplateView):
    template_name = 'pages/faq.html'

class PrivacyPolicyView(TemplateView):
    template_name = 'pages/privacy_policy.html'

class TermsView(TemplateView):
    template_name = 'pages/terms.html'

class BlogListView(ListView):
    model = BlogPost
    template_name = 'pages/blog_list.html'
    context_object_name = 'posts'
    paginate_by = 6

class BlogDetailView(DetailView):
    model = BlogPost
    template_name = 'pages/blog_detail.html'
    context_object_name = 'post'

class ReviewListView(ListView):
    model = Review
    template_name = 'pages/review_list.html'
    context_object_name = 'reviews'
    paginate_by = 10
    
    def get_queryset(self):
        return Review.objects.filter(is_approved=True).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['meals'] = Meal.objects.filter(is_available=True)
        return context

    def post(self, request, *args, **kwargs):
        meal_id = request.POST.get('meal')
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        full_name = request.POST.get('full_name') # For guest reviews
        
        if meal_id and rating and comment:
            meal = Meal.objects.get(id=meal_id)
            Review.objects.create(
                meal=meal,
                user=request.user if request.user.is_authenticated else None,
                rating=rating,
                comment=comment,
                is_approved=False # Admin must approve
            )
            return render(request, 'pages/review_success.html')
        
        return self.get(request, *args, **kwargs)

class TrainingView(CreateView):
    from .models import GraduationEventImage
    from .forms import TrainingApplicationForm
    
    template_name = 'pages/training.html'
    form_class = TrainingApplicationForm
    success_url = reverse_lazy('pages:training')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import GraduationEventImage
        context['graduation_images'] = GraduationEventImage.objects.all()
        return context

    def form_valid(self, form):
        from django.contrib import messages
        messages.success(self.request, "Your application has been submitted successfully! We'll contact you soon.")
        return super().form_valid(form)
