from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile, UserBranchReward

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'phone_number', 'is_staff')
    ordering = ('email',)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'birth_date', 'reward_points', 'points_earned_at')
    readonly_fields = ('reward_points', 'points_earned_at')

@admin.register(UserBranchReward)
class UserBranchRewardAdmin(admin.ModelAdmin):
    list_display = ('user', 'branch', 'points', 'points_earned_at', 'updated_at')
    list_filter = ('branch',)
    search_fields = ('user__email', 'branch__name')
    readonly_fields = ('user', 'branch', 'points', 'points_earned_at', 'updated_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
