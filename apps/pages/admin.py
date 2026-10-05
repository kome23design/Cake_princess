from django.contrib import admin
from .models import (
    BlogPost, TrainingApplication, GraduationEventImage, 
    MarqueeSetting, Branch, BranchHeroImage, BranchNavLink, Service, TrainingExplanation
)

class BranchHeroImageInline(admin.TabularInline):
    model = BranchHeroImage
    extra = 1

class BranchNavLinkInline(admin.TabularInline):
    model = BranchNavLink
    extra = 1

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'phone', 'address', 'is_default', 'is_active', 'order']
    list_editable = ['is_default', 'is_active', 'order']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'address', 'phone', 'email']
    inlines = [BranchHeroImageInline, BranchNavLinkInline]

@admin.register(BranchNavLink)
class BranchNavLinkAdmin(admin.ModelAdmin):
    list_display = ['title', 'branch', 'url', 'order', 'is_active']
    list_editable = ['url', 'order', 'is_active']
    list_filter = ['branch', 'is_active']
    search_fields = ['title', 'url']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['title', 'price_starting_at', 'icon', 'order', 'is_active', 'created_at']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active', 'branches']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['branches']
    search_fields = ['title', 'short_description', 'description']

@admin.register(TrainingExplanation)
class TrainingExplanationAdmin(admin.ModelAdmin):
    list_display = ['title', 'duration_info', 'schedule_info', 'is_active', 'updated_at']
    list_editable = ['is_active']

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'author', 'created_at']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'content']

@admin.register(TrainingApplication)
class TrainingApplicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'branch', 'email', 'phone', 'course_level', 'applied_at']
    list_filter = ['branch', 'course_level', 'applied_at']
    search_fields = ['name', 'email', 'phone']

@admin.register(GraduationEventImage)
class GraduationEventImageAdmin(admin.ModelAdmin):
    list_display = ['caption', 'event_date', 'uploaded_at']
    list_filter = ['event_date']

@admin.register(MarqueeSetting)
class MarqueeSettingAdmin(admin.ModelAdmin):
    list_display = ['text', 'branch', 'active']
    list_editable = ['active']
    list_filter = ['branch', 'active']
    search_fields = ['text']
