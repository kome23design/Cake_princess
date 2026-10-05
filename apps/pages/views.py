from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, CreateView
from django.http import JsonResponse, HttpResponseRedirect
from django.db.models import Q, Case, When, Value, IntegerField
from django.core.mail import send_mail
from django.contrib import messages
import datetime

from menu.models import Meal, Category, Review
from .models import BlogPost, Branch, Service, TrainingExplanation, GraduationEventImage
from .forms import TrainingApplicationForm


def get_current_branch(request):
    """Retrieve active selected branch or fallback to default."""
    slug = request.session.get('selected_branch_slug') or request.COOKIES.get('selected_branch_slug')
    bid = request.session.get('selected_branch_id')
    branch = None
    if slug:
        branch = Branch.objects.filter(slug=slug, is_active=True).first()
    elif bid:
        try:
            branch = Branch.objects.filter(id=int(bid), is_active=True).first()
        except (ValueError, TypeError):
            pass
    if not branch:
        branch = Branch.objects.filter(is_default=True, is_active=True).first() or Branch.objects.filter(is_active=True).first()
    return branch


class SetBranchView(View):
    """Endpoint to switch or select desired branch."""
    def get(self, request, slug):
        return self._set_branch(request, slug)

    def post(self, request, slug):
        return self._set_branch(request, slug)

    def _set_branch(self, request, slug):
        branch = get_object_or_404(Branch, slug=slug, is_active=True)
        request.session['selected_branch_id'] = branch.id
        request.session['selected_branch_slug'] = branch.slug
        request.session['branch_chosen_in_session'] = True

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            response = JsonResponse({
                'status': 'success',
                'branch_id': branch.id,
                'branch_name': branch.name,
                'branch_slug': branch.slug,
                'branch_address': branch.address,
                'branch_phone': branch.phone,
            })
        else:
            redirect_to = request.META.get('HTTP_REFERER') or str(reverse_lazy('pages:home'))
            if 'branch_prompt' in redirect_to or 'logged_out' in redirect_to:
                redirect_to = str(reverse_lazy('pages:home'))
            response = HttpResponseRedirect(redirect_to)

        # Set session-scoped cookies
        response.set_cookie('selected_branch_slug', branch.slug, samesite='Lax')
        response.set_cookie('selected_branch_id', str(branch.id), samesite='Lax')
        return response


class HomeView(TemplateView):
    template_name = 'pages/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = str(datetime.datetime.now().weekday())
        current_branch = get_current_branch(self.request)
        context['branch'] = current_branch

        # Hero images for this branch
        hero_images = []
        if current_branch:
            hero_images = list(current_branch.hero_images.all())
        context['branch_hero_images'] = hero_images

        # Filter categories by branch (either assigned to this branch or global)
        if current_branch:
            categories_qs = Category.objects.filter(
                Q(branches=current_branch) | Q(branches__isnull=True)
            ).distinct()
        else:
            categories_qs = Category.objects.all()
        context['categories'] = categories_qs

        # Filter featured meals by branch
        featured_qs = Meal.objects.filter(is_daily_special=True)
        if current_branch:
            featured_qs = featured_qs.filter(
                Q(branches=current_branch) | Q(branches__isnull=True)
            ).distinct()

        context['featured_meals'] = featured_qs.annotate(
            available_today=Case(
                When(available_days__contains=today, is_available=True, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).order_by('-available_today', '-created_at')[:6]

        # Reviews for this branch or global
        reviews_qs = Review.objects.filter(is_approved=True)
        if current_branch:
            reviews_qs = reviews_qs.filter(
                Q(branch=current_branch) | Q(branch__isnull=True)
            ).distinct()
        context['reviews'] = reviews_qs.order_by('-created_at')[:6]

        # Services offered preview (for home page highlight)
        if current_branch:
            services_qs = Service.objects.filter(is_active=True).filter(
                Q(branches=current_branch) | Q(branches__isnull=True)
            ).distinct().order_by('order', 'title')
        else:
            services_qs = Service.objects.filter(is_active=True).order_by('order', 'title')
        context['services'] = services_qs[:4]

        return context


class ServicesView(TemplateView):
    template_name = 'pages/services.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_branch = get_current_branch(self.request)
        if current_branch:
            services = Service.objects.filter(is_active=True).filter(
                Q(branches=current_branch) | Q(branches__isnull=True)
            ).distinct().order_by('order', 'title')
        else:
            services = Service.objects.filter(is_active=True).order_by('order', 'title')
        context['services'] = services
        context['active_branch'] = current_branch
        return context


class AboutView(TemplateView):
    template_name = 'pages/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['branches'] = Branch.objects.filter(is_active=True).order_by('order', 'name')
        context['current_branch'] = get_current_branch(self.request)
        return context


class ContactView(TemplateView):
    template_name = 'pages/contact.html'

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name', 'Unknown')
        email = request.POST.get('email', 'No Email')
        phone = request.POST.get('phone', 'No Phone')
        branch_name = request.POST.get('branch_name', 'General')
        subject = request.POST.get('subject', 'No Subject')
        message = request.POST.get('message', '')
        
        full_message = (
            f"Message from {name} ({email}, {phone})\n"
            f"Branch: {branch_name}\n"
            f"Subject: {subject}\n\n"
            f"{message}"
        )
        
        try:
            send_mail(
                subject=f"Contact Form [{branch_name}]: {subject}",
                message=full_message,
                from_email='noreply@cakeprincess.com',
                recipient_list=['hello@cakeprincess.com'],
                fail_silently=True,
            )
        except Exception:
            pass
            
        messages.success(request, "Your message has been sent successfully! We will get back to you shortly.")
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
        current_branch = get_current_branch(self.request)
        qs = Review.objects.filter(is_approved=True)
        if current_branch:
            qs = qs.filter(Q(branch=current_branch) | Q(branch__isnull=True)).distinct()
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_branch = get_current_branch(self.request)
        meals_qs = Meal.objects.filter(is_available=True)
        if current_branch:
            meals_qs = meals_qs.filter(Q(branches=current_branch) | Q(branches__isnull=True)).distinct()
        context['meals'] = meals_qs
        return context

    def post(self, request, *args, **kwargs):
        meal_id = request.POST.get('meal')
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        current_branch = get_current_branch(request)
        
        if meal_id and rating and comment:
            meal = Meal.objects.get(id=meal_id)
            Review.objects.create(
                meal=meal,
                branch=current_branch,
                user=request.user if request.user.is_authenticated else None,
                rating=rating,
                comment=comment,
                is_approved=False # Admin must approve
            )
            return render(request, 'pages/review_success.html')
        
        return self.get(request, *args, **kwargs)


class TrainingView(CreateView):
    template_name = 'pages/training.html'
    form_class = TrainingApplicationForm
    success_url = reverse_lazy('pages:training')

    def get_initial(self):
        initial = super().get_initial()
        current_branch = get_current_branch(self.request)
        if current_branch:
            initial['branch'] = current_branch.id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['graduation_images'] = GraduationEventImage.objects.all()
        context['training_explanation'] = TrainingExplanation.objects.filter(is_active=True).first()
        return context

    def form_valid(self, form):
        application = form.save()
        branch_name = application.branch.name if application.branch else "Selected Branch"
        messages.success(
            self.request, 
            f"Your application for {branch_name} has been submitted successfully! We'll contact you soon."
        )
        return super().form_valid(form)
