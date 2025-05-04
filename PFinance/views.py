from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Count, Prefetch, Q, Sum
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, CreateView, UpdateView, DetailView, DeleteView, ListView

from PFinance.forms import SignUpForm, ProfileEditForm, BudgetForm, TransactionForm
from PFinance.models import UserProfile, Alert, Budget, Transaction


# Vista para el panel
class DashboardView(LoginRequiredMixin, TemplateView):
    model = UserProfile
    template_name = 'pfinance/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Optimización con prefetch_related y annotate
        user_with_alerts = User.objects.filter(pk=user.pk).prefetch_related(
            Prefetch(
                'alerts',
                queryset=Alert.objects.order_by('-created_at')[:5],  # Solo las 5 más recientes
                to_attr='recent_alerts'
            )
        ).annotate(
            unread_count=Count('alerts', filter=Q(alerts__read=False))
        ).first()

        context["usuario"] = user_with_alerts.profile
        context['unread_count'] = user_with_alerts.unread_count
        context['recent_alerts'] = user_with_alerts.recent_alerts
        
        return context


# Vista de registro
class SignUpView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy('pfinance:dashboard')
    template_name = 'registration/register.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


# Vista para ver los detalles del perfil
class ProfileView(LoginRequiredMixin, DetailView):
    model = UserProfile
    template_name = 'pfinance/profile_detail.html'
    context_object_name = 'profile'

    def get_object(self):
        return self.request.user.profile


# Vista para editar el perfil
class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = ProfileEditForm
    template_name = 'pfinance/profile_edit.html'
    success_url = reverse_lazy('pfinance:profile')

    def get_object(self):
        return self.request.user.profile

    def form_valid(self, form):
        messages.success(self.request, "Perfil actualizado correctamente!")
        return super().form_valid(form)


# Vista para listar alertas
class AlertsListView(LoginRequiredMixin, TemplateView):
    model = Alert
    template_name = 'pfinance/alerts_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['alerts'] = self.request.user.alerts.all().order_by('-created_at')
        return context


# Vista para los detalles de las alertas
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


# Vista para la lista de presupuestos
class BudgetListView(LoginRequiredMixin, ListView):
    model = Budget
    template_name = 'pfinance/budgets_list.html'
    context_object_name = 'budgets'

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user).select_related('category')

# Vista para crear presupuestos
class BudgetCreateView(LoginRequiredMixin, CreateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'pfinance/budgets_create.html'
    success_url = reverse_lazy('pfinance:budgets_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

# Vista para editar presupuestos
class BudgetUpdateView(LoginRequiredMixin, UpdateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'pfinance/budgets_update.html'
    success_url = reverse_lazy('pfinance:budgets_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Presupuesto actualizado exitosamente")
        return super().form_valid(form)

# Vista para borrar presupuestos
class BudgetDeleteView(LoginRequiredMixin, DeleteView):
    model = Budget
    template_name = 'pfinance/budgets_delete.html'
    success_url = reverse_lazy('pfinance:budgets_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Presupuesto eliminado exitosamente")
        return super().delete(request, *args, **kwargs)


# Vista para la lista de transacciones
class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'pfinance/transactions_list.html'
    context_object_name = 'transactions'
    paginate_by = 15

    def get_queryset(self):
        queryset = Transaction.objects.filter(
            user=self.request.user
        ).select_related('category').order_by('-date')

        # Filtro por tipo (gasto/ingreso)
        transaction_type = self.request.GET.get('type')
        if transaction_type == 'expense':
            queryset = queryset.filter(is_expense=True)
        elif transaction_type == 'income':
            queryset = queryset.filter(is_expense=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Totales para resumen
        context['total_expenses'] = Transaction.objects.filter(
            user=user, is_expense=True
        ).aggregate(total=Sum('amount'))['total'] or 0

        context['total_income'] = Transaction.objects.filter(
            user=user, is_expense=False
        ).aggregate(total=Sum('amount'))['total'] or 0

        context['balance'] = context['total_income'] - context['total_expenses']

        return context


# Vista para crear transacciones
class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'pfinance/transactions_create.html'
    success_url = reverse_lazy('pfinance:transactions_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


# Vista para editar transacciones
class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'pfinance/transactions_update.html'
    success_url = reverse_lazy('pfinance:transactions_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        return super().form_valid(form)


# Vista para borrar transacciones
class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    template_name = 'pfinance/transactions_delete.html'
    success_url = reverse_lazy('pfinance:transactions_list')

    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)



