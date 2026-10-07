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
    success_url = reverse_lazy('accounts:profile')

    def form_valid(self, form):
        from django.contrib.auth import login
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ensure profile exists
        profile, _ = Profile.objects.get_or_create(user=self.request.user)

        # Compute branch-specific points info
        from pages.views import get_current_branch
        current_branch = get_current_branch(self.request)
        branch_points = 0
        branch_reward = None
        points_expiry_date = None
        points_days_left = None

        if current_branch:
            branch_reward = self.request.user.branch_rewards.filter(branch=current_branch).first()
            if branch_reward:
                from orders.models import RewardSetting
                setting = RewardSetting.objects.filter(branch=current_branch).first() or RewardSetting.objects.first()
                if setting and setting.points_expiry_days and branch_reward.points > 0:
                    branch_reward.check_and_expire_points(setting.points_expiry_days)
                    branch_reward.refresh_from_db()
                    if branch_reward.points > 0 and branch_reward.points_earned_at:
                        points_expiry_date = branch_reward.points_earned_at + timezone.timedelta(
                            days=setting.points_expiry_days
                        )
                        delta = points_expiry_date - timezone.now()
                        points_days_left = max(0, delta.days)
                branch_points = branch_reward.points

        all_branch_rewards = list(self.request.user.branch_rewards.select_related('branch').all())
        
        # Build comprehensive branch selection list with user points
        from pages.models import Branch
        all_active_branches = list(Branch.objects.filter(is_active=True).order_by('order', 'name'))
        branch_rewards_map = {br.branch_id: br for br in self.request.user.branch_rewards.all()}
        branches_with_info = []
        for b in all_active_branches:
            rw = branch_rewards_map.get(b.id)
            branches_with_info.append({
                'branch': b,
                'is_current': bool(current_branch and b.id == current_branch.id),
                'points': rw.points if rw else 0,
                'reward': rw
            })

        context['profile'] = profile
        context['current_branch'] = current_branch
        context['branch_points'] = branch_points
        context['branch_reward'] = branch_reward
        context['all_branch_rewards'] = all_branch_rewards
        context['branches_with_info'] = branches_with_info
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
        return self._do_logout(request)

    def post(self, request):
        return self._do_logout(request)

    def _do_logout(self, request):
        logout(request)
        request.session.flush()
        from django.urls import reverse
        home_url = reverse('pages:home') + '?logged_out=1&branch_prompt=1'
        response = redirect(home_url)
        response.delete_cookie('selected_branch_slug')
        response.delete_cookie('selected_branch_id')
        return response

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

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .models import PushSubscription

@csrf_exempt
def save_push_subscription(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            endpoint = data.get('endpoint')
            keys = data.get('keys', {})
            p256dh = keys.get('p256dh')
            auth = keys.get('auth')

            if not endpoint or not p256dh or not auth:
                return JsonResponse({'status': 'error', 'message': 'Invalid subscription data'}, status=400)

            user = request.user if request.user.is_authenticated else None
            if not user or not user.is_staff:
                return JsonResponse({'status': 'error', 'message': 'Unauthorized. Admin only.'}, status=403)

            sub, created = PushSubscription.objects.update_or_create(
                endpoint=endpoint,
                defaults={
                    'user': user,
                    'p256dh': p256dh,
                    'auth': auth,
                }
            )
            return JsonResponse({'status': 'success', 'message': 'Subscription saved'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

def vapid_public_key(request):
    from django.conf import settings
    return JsonResponse({'public_key': getattr(settings, 'VAPID_PUBLIC_KEY', '')})
