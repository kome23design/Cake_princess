from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import CreateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, logout
from .forms import UserRegisterForm, EditProfileForm, ChangePasswordForm
from .models import Profile

class RegisterView(CreateView):
    form_class = UserRegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ensure profile exists
        profile, _ = Profile.objects.get_or_create(user=self.request.user)

        # Compute points expiry info
        points_expiry_date = None
        points_days_left = None
        try:
            from orders.models import RewardSetting
            setting = RewardSetting.objects.first()
            if setting and setting.points_expiry_days and profile.reward_points > 0:
                # Backfill points_earned_at for legacy profiles that have points but no timestamp
                if not profile.points_earned_at:
                    profile.points_earned_at = timezone.now()
                    profile.save(update_fields=['points_earned_at'])

                # Auto-expire if window has passed
                profile.check_and_expire_points(setting.points_expiry_days)
                # Refresh from DB in case expiry just ran
                profile.refresh_from_db()

                if profile.reward_points > 0 and profile.points_earned_at:
                    points_expiry_date = profile.points_earned_at + timezone.timedelta(
                        days=setting.points_expiry_days
                    )
                    delta = points_expiry_date - timezone.now()
                    points_days_left = max(0, delta.days)
        except Exception:
            pass

        context['profile'] = profile
        context['points_expiry_date'] = points_expiry_date
        context['points_days_left'] = points_days_left
        context['edit_form'] = EditProfileForm(instance=self.request.user)
        context['password_form'] = ChangePasswordForm()
        return context


class EditProfileView(LoginRequiredMixin, View):
    def get(self, request):
        form = EditProfileForm(instance=request.user)
        return render(request, 'accounts/edit_profile.html', {'form': form})

    def post(self, request):
        form = EditProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
        return render(request, 'accounts/edit_profile.html', {'form': form})


class CustomLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('pages:home')

    def post(self, request):
        logout(request)
        return redirect('pages:home')

class ChangePasswordView(LoginRequiredMixin, View):
    def get(self, request):
        form = ChangePasswordForm()
        return render(request, 'accounts/change_password.html', {'form': form})

    def post(self, request):
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            old_password = form.cleaned_data['old_password']
            new_password = form.cleaned_data['new_password1']
            if not request.user.check_password(old_password):
                messages.error(request, 'Current password is incorrect.')
                return render(request, 'accounts/change_password.html', {'form': form})
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password changed successfully!')
            return redirect('accounts:profile')
        return render(request, 'accounts/change_password.html', {'form': form})
