from django.views.generic import CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Reservation
from .forms import ReservationForm

class ReservationCreateView(CreateView):
    model = Reservation
    form_class = ReservationForm
    template_name = 'reservations/reservation_form.html'
    success_url = reverse_lazy('reservations:reservation_list')

    def get_initial(self):
        initial = super().get_initial()
        from pages.models import Branch
        slug = self.request.session.get('selected_branch_slug') or self.request.COOKIES.get('selected_branch_slug')
        bid = self.request.session.get('selected_branch_id')
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
        if branch:
            initial['branch'] = branch.id
        return initial

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.user = self.request.user
        return super().form_valid(form)

class ReservationListView(ListView):
    model = Reservation
    template_name = 'reservations/reservation_list.html'
    context_object_name = 'reservations'

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Reservation.objects.filter(user=self.request.user)
        return Reservation.objects.none()
