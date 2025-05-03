from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views
from .views import SignUpView, ProfileUpdateView, ProfileView

app_name = 'pfinance'

urlpatterns = [
    # Autenticación y dashboard
    path("", views.DashboardView.as_view(), name="dashboard"),
    path('register/', SignUpView.as_view(template_name='registration/register.html'), name='register'),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(template_name='registration/logout.html'), name='logout'),

    # Perfil
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', ProfileUpdateView.as_view(), name='profile_edit'),

    # Alertas
    path('alerts/', views.AlertsListView.as_view(), name='alerts'),
    path('alerts/<int:alert_id>/', views.AlertDetailView.as_view(), name='alert_detail'),
    path('alerts/mark-read/', views.MarkAlertsReadView.as_view(), name='mark_alerts_read'),


    # path('transactions/', views.TransactionsView.as_view(), name='transactions'),
    # path('budgets/', views.BudgetsView.as_view(), name='budgets'),
    # path('recurring-payments/', views.RecurringPaymentsView.as_view(), name='recurring_payments'),
]