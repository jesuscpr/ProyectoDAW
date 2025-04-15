from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views
from .views import SignUpView

app_name = 'pfinance'

urlpatterns = [
    # Página principal y dashboard
    path("", views.DashboardView.as_view(), name="dashboard"),
    path('register/', SignUpView.as_view(template_name='registration/register.html'), name='register'),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(template_name='registration/logged_out.html'), name='logout'),
]