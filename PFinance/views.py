from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, CreateView, UpdateView, DetailView

from PFinance.forms import SignUpForm, ProfileEditForm
from PFinance.models import UserProfile, Alert


class DashboardView(LoginRequiredMixin, TemplateView):
    model = UserProfile
    template_name = 'pfinance/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["usuario"] = self.request.user.profile
        context['unread_alerts'] = self.request.user.alerts.filter(read=False).count()
        return context

class SignUpView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy('pfinance:dashboard')
    template_name = 'registration/register.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class ProfileView(LoginRequiredMixin, DetailView):
    model = UserProfile
    template_name = 'pfinance/profile_detail.html'
    context_object_name = 'profile'

    def get_object(self):
        return self.request.user.profile


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = ProfileEditForm
    template_name = 'pfinance/profile_edit.html'
    success_url = reverse_lazy('pfinance:dashboard')

    def get_object(self):
        # Obtiene el perfil del usuario actual
        return self.request.user.profile


# Vista para listar alertas
class AlertsListView(LoginRequiredMixin, TemplateView):
    model = Alert
    template_name = 'pfinance/alerts_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['alerts'] = self.request.user.alerts.all().order_by('-created_at')
        return context


# Vista para detalle de alerta
class AlertDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'pfinance/alerts_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        alert_id = self.kwargs.get('alert_id')
        alert = self.request.user.alerts.get(id=alert_id)
        if not alert.read:
            alert.read = True
            alert.save(update_fields=['read'])
        context['alert'] = alert
        return context


# Vista para marcar alertas como leídas (API)
@method_decorator([login_required, require_POST], name='dispatch')
class MarkAlertsReadView(TemplateView):
    def post(self, request, *args, **kwargs):
        updated = request.user.alerts.filter(read=False).update(read=True)
        return JsonResponse({'status': 'success', 'updated': updated})