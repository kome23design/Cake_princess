from django.contrib import admin
from .models import BlogPost, TeamMember, TrainingApplication, GraduationEventImage

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'author', 'created_at']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'content']

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'order']
    list_editable = ['order']

@admin.register(TrainingApplication)
class TrainingApplicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'course_level', 'applied_at']
    list_filter = ['course_level', 'applied_at']
    search_fields = ['name', 'email', 'phone']

@admin.register(GraduationEventImage)
class GraduationEventImageAdmin(admin.ModelAdmin):
    list_display = ['caption', 'event_date', 'uploaded_at']
    list_filter = ['event_date']
