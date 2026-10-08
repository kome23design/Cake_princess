from django.contrib import admin
from .models import Category, Meal, Review, MealImage, MadeOnCommandItem, MadeOnCommandInquiry

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['branches']

class MealImageInline(admin.TabularInline):
    model = MealImage
    extra = 1

@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'display_branches', 'available_days', 'is_available', 'is_daily_special', 'created_at']
    list_filter = ['branches', 'is_available', 'is_daily_special', 'category', 'created_at']
    list_editable = ['price', 'available_days', 'is_available', 'is_daily_special']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['branches']
    search_fields = ['name', 'description']
    inlines = [MealImageInline]

    def display_branches(self, obj):
        branches = obj.branches.all()
        if not branches.exists():
            return "All Branches (Global)"
        return ", ".join([b.name for b in branches])
    display_branches.short_description = "Branches"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        branch_id = request.GET.get('branch')
        if branch_id:
            try:
                qs = qs.filter(branches__id=int(branch_id))
            except (ValueError, TypeError):
                pass
        return qs

    def changelist_view(self, request, extra_context=None):
        from pages.models import Branch
        extra_context = extra_context or {}
        branch_id = request.GET.get('branch')
        active_branch = None
        if branch_id:
            try:
                active_branch = Branch.objects.filter(id=int(branch_id)).first()
            except (ValueError, TypeError):
                pass

        extra_context['branch_list'] = Branch.objects.filter(is_active=True).order_by('order', 'name')
        extra_context['active_branch'] = active_branch
        return super().changelist_view(request, extra_context=extra_context)

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        branch_id = request.GET.get('branch')
        if branch_id:
            try:
                initial['branches'] = [int(branch_id)]
            except (ValueError, TypeError):
                pass
        return initial

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['meal', 'branch', 'user', 'rating', 'is_approved', 'created_at']
    list_filter = ['branch', 'is_approved', 'rating', 'created_at']
    list_editable = ['is_approved']
    actions = ['approve_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Approve selected reviews"

@admin.register(MadeOnCommandItem)
class MadeOnCommandItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']
    list_editable = ['is_active']
    prepopulated_fields = {'slug': ('title',)}

@admin.register(MadeOnCommandInquiry)
class MadeOnCommandInquiryAdmin(admin.ModelAdmin):
    list_display = ['name', 'item', 'email', 'phone', 'event_date', 'created_at']
    list_filter = ['item', 'event_date', 'created_at']
    search_fields = ['name', 'email', 'phone', 'message']

