from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView, UpdateView, DetailView, DeleteView, ListView, View


from PFinance.forms import *

from PFinance.models import UserProfile, Alert, Budget, Transaction, RecurringPayment, RecurringIncome, Goal


# Vista para el panel
class DashboardView(LoginRequiredMixin, TemplateView):
    model = UserProfile
    template_name = 'pfinance/dashboard.html'


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
        transactions = alert.transactions.all()
        if not alert.read:
            alert.read = True
            alert.save(update_fields=['read'])
        context['alert'] = alert
        context['transactions'] = transactions
        return context


# Vista para eliminar la alerta
class AlertDeleteView(LoginRequiredMixin, DeleteView):
    model = Alert
    template_name = 'pfinance/alerts_delete.html'
    success_url = reverse_lazy('pfinance:alerts')

    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


# Vista para marcar alertas como leídas
class MarkAlertReadView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        alert_id = kwargs.get('pk')
        alert = get_object_or_404(Alert, pk=alert_id, user=request.user)
        if not alert.read:
            alert.read = True
            alert.save()
        return redirect('pfinance:alerts')


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


# Vista para borrar transacciones
class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    template_name = 'pfinance/transactions_delete.html'
    success_url = reverse_lazy('pfinance:transactions_list')

    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


# Vista para la lista de pagos recurrentes
class RecurringPaymentListView(LoginRequiredMixin, ListView):
    model = RecurringPayment
    template_name = 'pfinance/recurring_payments_list.html'
    context_object_name = 'payments'

    def get_queryset(self):
        return self.request.user.recurring_payments.select_related('category').order_by('next_due_date')


# Vista para crear pagos recurrentes
class RecurringPaymentCreateView(LoginRequiredMixin, CreateView):
    model = RecurringPayment
    form_class = RecurringPaymentForm
    template_name = 'pfinance/recurring_payments_create.html'
    success_url = reverse_lazy('pfinance:recurring_payments')

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f"Pago recurrente '{self.object.name}' creado exitosamente")
        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


# Vista para eliminar pagos recurrentes
class RecurringPaymentDeleteView(LoginRequiredMixin, DeleteView):
    model = RecurringPayment
    template_name = 'pfinance/recurring_payments_delete.html'
    success_url = reverse_lazy('pfinance:recurring_payments')
    context_object_name = 'payment'

    def get_queryset(self):
        return self.request.user.recurring_payments

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Pago recurrente '{self.object.name}' eliminado exitosamente")
        return response


# Vista para la lista de ingresos recurrentes
class RecurringIncomeListView(LoginRequiredMixin, ListView):
    model = RecurringIncome
    template_name = 'pfinance/recurring_income_list.html'
    context_object_name = 'incomes'
    paginate_by = 10

    def get_queryset(self):
        return self.request.user.recurring_incomes.select_related('category').order_by('next_income_date')


# Vista para crear ingresos recurrentes
class RecurringIncomeCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = RecurringIncome
    form_class = RecurringIncomeForm
    template_name = 'pfinance/recurring_income_create.html'
    success_url = reverse_lazy('pfinance:recurring_income_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


# Vista para borrar ingresos recurrentes
class RecurringIncomeDeleteView(LoginRequiredMixin, DeleteView):
    model = RecurringIncome
    template_name = 'pfinance/recurring_income_confirm_delete.html'
    success_url = reverse_lazy('pfinance:recurring_income_list')
    context_object_name = 'income'

    def get_queryset(self):
        return self.request.user.recurring_incomes


# Vista para la lista de metas
class GoalListView(LoginRequiredMixin, ListView):
    model = Goal
    template_name = 'pfinance/goal_list.html'
    context_object_name = 'goals'
    paginate_by = 10

    def get_queryset(self):
        return self.request.user.goals.all()


# Vista para crear metas
class GoalCreateView(LoginRequiredMixin, CreateView):
    model = Goal
    form_class = GoalForm
    template_name = 'pfinance/goal_create.html'
    success_url = reverse_lazy('pfinance:goals_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


# Vista para actualizar el monto de las metas
class GoalUpdateAmountView(LoginRequiredMixin, UpdateView):
    model = Goal
    form_class = GoalAmountUpdateForm
    template_name = 'pfinance/goal_update_amount.html'
    success_url = reverse_lazy('pfinance:goals_list')

    def get_queryset(self):
        return self.request.user.goals.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['progress_percentage'] = self.object.progress_percentage()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)

        # Verificación adicional en la vista
        if self.object.current_amount >= self.object.target_amount:
            messages.success(
                self.request,
                f"¡Felicidades! Has alcanzado tu meta: {self.object.subject}"
            )
        return response


# Vista para borrar una meta
class GoalDeleteView(LoginRequiredMixin, DeleteView):
    model = Goal
    template_name = 'pfinance/goal_confirm_delete.html'
    success_url = reverse_lazy('pfinance:goals_list')

    def get_queryset(self):
        return self.request.user.goals.all()



