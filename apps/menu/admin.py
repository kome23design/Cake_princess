from django.contrib import admin
from .models import Category, Meal, Review, MealImage, MadeOnCommandItem, MadeOnCommandInquiry

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

class MealImageInline(admin.TabularInline):
    model = MealImage
    extra = 1

@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'available_days', 'is_available', 'is_daily_special', 'created_at']
    list_filter = ['is_available', 'is_daily_special', 'category', 'created_at']
    list_editable = ['price', 'available_days', 'is_available', 'is_daily_special']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    inlines = [MealImageInline]

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['meal', 'user', 'rating', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'rating', 'created_at']
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

