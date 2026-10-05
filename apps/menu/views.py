from django.views.generic import ListView, DetailView
from django.shortcuts import redirect
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
        import datetime
        from django.db.models import Case, When, Value, IntegerField
        from pages.views import get_current_branch
        
        today = str(datetime.datetime.now().weekday())
        current_branch = get_current_branch(self.request)
        
        queryset = Meal.objects.all()
        if current_branch:
            queryset = queryset.filter(Q(branches=current_branch) | Q(branches__isnull=True)).distinct()

        queryset = queryset.annotate(
            available_today=Case(
                When(available_days__contains=today, is_available=True, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).order_by('-available_today', '-created_at')
        
        category_slug = self.kwargs.get('slug')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from pages.views import get_current_branch
        current_branch = get_current_branch(self.request)
        if current_branch:
            categories_qs = Category.objects.filter(
                Q(branches=current_branch) | Q(branches__isnull=True)
            ).distinct()
        else:
            categories_qs = Category.objects.all()
        context['categories'] = categories_qs
        current_cat_slug = self.kwargs.get('slug')
        context['current_category'] = current_cat_slug
        context['current_branch'] = current_branch
        
        if current_cat_slug in ['cakes', 'pastries', 'event-packages']:
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
        import urllib.parse
        self.object = self.get_object()
        form = MadeOnCommandInquiryForm(request.POST)
        if form.is_valid():
            inquiry = form.save(commit=False)
            inquiry.item = self.object
            inquiry.save()

            from pages.views import get_current_branch
            current_branch = get_current_branch(request)
            branch_name = current_branch.name if current_branch else "General"
            admin_phone = "237621643169"

            event_date_str = inquiry.event_date.strftime('%A, %B %d, %Y') if inquiry.event_date else 'Flexible / To be confirmed'
            whatsapp_text = (
                f"👑 *NEW MADE-ON-COMMAND INQUIRY* 👑\n\n"
                f"🎂 *Item:* {self.object.title}\n"
                f"📁 *Category:* {self.object.category.name}\n"
                f"📍 *Branch:* {branch_name}\n"
                f"👤 *Client Name:* {inquiry.name}\n"
                f"📞 *Phone:* {inquiry.phone}\n"
                f"📧 *Email:* {inquiry.email}\n"
                f"📅 *Event Date:* {event_date_str}\n\n"
                f"📝 *Details & Special Requests:*\n{inquiry.message}\n\n"
                f"Please reply with availability and quotation!"
            )
            encoded = urllib.parse.quote(whatsapp_text)
            whatsapp_url = f"https://wa.me/{admin_phone}?text={encoded}"
            return redirect(whatsapp_url)
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)

class MealDetailView(DetailView):
    model = Meal
    template_name = 'menu/meal_detail.html'
    context_object_name = 'meal'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.category.slug == 'event-packages':
            context['inquiry_form'] = MadeOnCommandInquiryForm()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.category.slug == 'event-packages':
            form = MadeOnCommandInquiryForm(request.POST)
            name = request.POST.get('name', '')
            email = request.POST.get('email', '')
            phone = request.POST.get('phone', '')
            event_date = request.POST.get('event_date', '')
            message = request.POST.get('message', '')

            # Save in database under matching MadeOnCommandItem
            cmd_item = MadeOnCommandItem.objects.filter(category=self.object.category).first()
            if cmd_item:
                from .models import MadeOnCommandInquiry
                import datetime
                parsed_date = None
                if event_date:
                    try:
                        parsed_date = datetime.date.fromisoformat(event_date)
                    except ValueError:
                        parsed_date = None
                MadeOnCommandInquiry.objects.create(
                    item=cmd_item,
                    name=name,
                    email=email,
                    phone=phone,
                    event_date=parsed_date,
                    message=f"[{self.object.name}] {message}"
                )

            import urllib.parse
            from pages.views import get_current_branch
            current_branch = get_current_branch(request)
            branch_name = current_branch.name if current_branch else "Yaoundé Palace"
            admin_phone = "237621643169"

            whatsapp_text = (
                f"👑 *NEW EVENT PACKAGE INQUIRY* 👑\n\n"
                f"🎉 *Package:* {self.object.name}\n"
                f"📍 *Branch:* {branch_name}\n"
                f"👤 *Client Name:* {name}\n"
                f"📞 *Phone:* {phone}\n"
                f"📧 *Email:* {email}\n"
                f"📅 *Event Date:* {event_date or 'To be confirmed'}\n\n"
                f"📝 *Details & Special Requests:*\n{message}\n\n"
                f"Please reply with availability and quotation!"
            )
            encoded = urllib.parse.quote(whatsapp_text)
            whatsapp_url = f"https://wa.me/{admin_phone}?text={encoded}"
            return redirect(whatsapp_url)
        return self.get(request, *args, **kwargs)

class MealSearchView(ListView):
    model = Meal
    template_name = 'menu/menu_list.html'
    context_object_name = 'meals'

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            import datetime
            from django.db.models import Case, When, Value, IntegerField
            from pages.views import get_current_branch
            
            today = str(datetime.datetime.now().weekday())
            current_branch = get_current_branch(self.request)
            
            qs = Meal.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
            if current_branch:
                qs = qs.filter(Q(branches=current_branch) | Q(branches__isnull=True)).distinct()

            return qs.annotate(
                available_today=Case(
                    When(available_days__contains=today, is_available=True, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).order_by('-available_today', '-created_at')
        return Meal.objects.none()
