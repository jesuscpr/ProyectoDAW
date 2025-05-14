from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views
from .views import SignUpView, ProfileUpdateView, ProfileView, BudgetListView, BudgetCreateView, BudgetUpdateView, \
    BudgetDeleteView, TransactionListView, TransactionCreateView, TransactionUpdateView, TransactionDeleteView

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
    path('alerts/<int:pk>/mark-read/', views.MarkAlertReadView.as_view(), name='mark_alerts_read'),
    path('alerts/<int:pk>/delete/', views.AlertDeleteView.as_view(), name='alert_delete'),


    # Transacciones
    path('transactions/', TransactionListView.as_view(), name='transactions_list'),
    path('transactions/create/', TransactionCreateView.as_view(), name='transactions_create'),
    path('transactions/<int:pk>/update/', TransactionUpdateView.as_view(), name='transactions_update'),
    path('transactions/<int:pk>/delete/', TransactionDeleteView.as_view(), name='transactions_delete'),


    # Presupuestos
    path('budgets/', BudgetListView.as_view(), name='budgets_list'),
    path('budgets/create/', BudgetCreateView.as_view(), name='budgets_create'),
    path('budgets/<int:pk>/update/', BudgetUpdateView.as_view(), name='budgets_update'),
    path('budgets/<int:pk>/delete/', BudgetDeleteView.as_view(), name='budgets_delete'),


    # path('recurring-payments/', views.RecurringPaymentsView.as_view(), name='recurring_payments'),
]