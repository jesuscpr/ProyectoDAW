from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView

from PFinance.forms import SignUpForm
from PFinance.models import UserProfile


# Create your views here.

class DashboardView(LoginRequiredMixin, TemplateView):
    model = UserProfile
    template_name = 'pfinance/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["usuario"] = self.request.user.profile
        return context

class SignUpView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy('pfinance:dashboard')
    template_name = 'registration/register.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response