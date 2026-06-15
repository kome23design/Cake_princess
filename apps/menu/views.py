from django.views.generic import ListView, DetailView
from django.db.models import Q
from .models import Meal, Category, MadeOnCommandItem
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import MadeOnCommandInquiryForm

class MenuListView(ListView):
    model = Meal
    template_name = 'menu/menu_list.html'
    context_object_name = 'meals'
    paginate_by = 12

    def get_queryset(self):
        queryset = Meal.objects.all()
        category_slug = self.kwargs.get('slug')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        current_cat_slug = self.kwargs.get('slug')
        context['current_category'] = current_cat_slug
        
        if current_cat_slug in ['cakes', 'pastries']:
            context['made_on_command_items'] = MadeOnCommandItem.objects.filter(
                category__slug=current_cat_slug, 
                is_active=True
            )
        return context

class MadeOnCommandDetailView(DetailView):
    model = MadeOnCommandItem
    template_name = 'menu/custom_item_detail.html'
    context_object_name = 'item'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = MadeOnCommandInquiryForm()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = MadeOnCommandInquiryForm(request.POST)
        if form.is_valid():
            inquiry = form.save(commit=False)
            inquiry.item = self.object
            inquiry.save()
            messages.success(request, "Your inquiry has been sent successfully! We'll contact you soon.")
            return self.get(request, *args, **kwargs)
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)

class MealDetailView(DetailView):
    model = Meal
    template_name = 'menu/meal_detail.html'
    context_object_name = 'meal'

class MealSearchView(ListView):
    model = Meal
    template_name = 'menu/menu_list.html'
    context_object_name = 'meals'

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return Meal.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
        return Meal.objects.none()
