from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView, UpdateView, DetailView

from PFinance.forms import SignUpForm, ProfileEditForm
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