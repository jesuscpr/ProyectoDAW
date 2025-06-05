from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views


app_name = 'pfinance'

urlpatterns = [
    # Autenticación, dashboard y landing page
    path('dashboard/', views.DashboardView.as_view(), name="dashboard"),
    path('register/', views.SignUpView.as_view(template_name='registration/register.html'), name='register'),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(template_name='registration/logout.html'), name='logout'),
    path('', views.LandingPageView.as_view(), name="landing"),


    # Perfil
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),


    # Alertas
    path('alerts/', views.AlertsListView.as_view(), name='alerts'),
    path('alerts/<int:alert_id>/', views.AlertDetailView.as_view(), name='alert_detail'),
    path('alerts/<int:pk>/mark-read/', views.MarkAlertReadView.as_view(), name='mark_alerts_read'),
    path('alerts/<int:pk>/delete/', views.AlertDeleteView.as_view(), name='alert_delete'),


    # Transacciones
    path('transactions/', views.TransactionListView.as_view(), name='transactions_list'),
    path('transactions/create/', views.TransactionCreateView.as_view(), name='transactions_create'),
    path('transactions/<int:pk>/delete/', views.TransactionDeleteView.as_view(), name='transactions_delete'),


    # Presupuestos
    path('budgets/', views.BudgetListView.as_view(), name='budgets_list'),
    path('budgets/create/', views.BudgetCreateView.as_view(), name='budgets_create'),
    path('budgets/<int:pk>/delete/', views.BudgetDeleteView.as_view(), name='budgets_delete'),


    # Pagos recurrentes
    path('recurring-payments/', views.RecurringPaymentListView.as_view(), name='recurring_payments'),
    path('recurring-payments/create/', views.RecurringPaymentCreateView.as_view(), name='recurring_payment_create'),
    path('recurring-payments/<int:pk>/delete/', views.RecurringPaymentDeleteView.as_view(), name='recurring_payment_delete'),


    # Ingresos recurrentes
    path('recurring-incomes/', views.RecurringIncomeListView.as_view(), name='recurring_income_list'),
    path('recurring-incomes/create/', views.RecurringIncomeCreateView.as_view(), name='recurring_income_create'),
    path('recurring-incomes/<int:pk>/delete/', views.RecurringIncomeDeleteView.as_view(), name='recurring_income_delete'),


    # Metas
    path('goals/', views.GoalListView.as_view(), name='goals_list'),
    path('goals/create/', views.GoalCreateView.as_view(), name='goals_create'),
    path('goals/<int:pk>/delete/', views.GoalDeleteView.as_view(), name='goal_delete'),
    path('<int:pk>/edit/', views.GoalUpdateAmountView.as_view(), name='goal_edit'),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)