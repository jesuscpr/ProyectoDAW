from datetime import date

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator


class Category(models.Model):
    """Categorías para clasificar transacciones (gastos o ingresos)"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)  # Para almacenar nombres de iconos
    is_expense = models.BooleanField(default=True)  # True: gasto, False: ingreso

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


CURRENCY_CHOICES = [
        ('EUR', 'Euro (€)'),
        ('USD', 'Dólar (US$)'),
        ('GBP', 'Libra (£)'),
    ]


class UserProfile(models.Model):
    """Perfil extendido del usuario con información financiera adicional"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    monthly_income = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='EUR')
    # notification_email = models.BooleanField(default=True) (Próximamente)
    notification_app = models.BooleanField(default=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"


class Transaction(models.Model):
    """Modelo para registrar todas las transacciones (gastos e ingresos)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='transactions')
    date = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True, null=True)
    is_expense = models.BooleanField(default=True)  # True: gasto, False: ingreso

    def __str__(self):
        transaction_type = "Gasto" if self.is_expense else "Ingreso"
        return f"{transaction_type}: {self.amount} - {self.category}"

    class Meta:
        ordering = ['-date']  # Ordenar por fecha descendente


class Budget(models.Model):
    """Presupuestos por categoría"""

    FREQUENCY_CHOICES = [
        ('monthly', 'Mensual'),
        ('yearly', 'Anual'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budgets')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    frequency = models.CharField( max_length=10, choices=FREQUENCY_CHOICES, default='MENSUAL')
    is_active = models.BooleanField(default=True)

    def spent_amount(self):
        return Transaction.objects.filter(
            user=self.user,
            category=self.category,
            is_expense=True
        ).aggregate(total=models.Sum('amount'))['total'] or 0

    def remaining_amount(self):
        return self.amount - self.spent_amount()

    def __str__(self):
        return f"Presupuesto: {self.category.name} - {self.amount}"


class RecurringPayment(models.Model):
    """Pagos recurrentes programados (suscripciones, facturas, etc.)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recurring_payments')
    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    FREQUENCY_CHOICES = [
        ('monthly', 'Mensual'),
        ('yearly', 'Anual'),
    ]
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='monthly')
    next_due_date = models.DateField()
    reminder_days = models.PositiveSmallIntegerField(default=3)  # Días antes para recordatorio

    is_active = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Pago recurrente"
        verbose_name_plural = "Pagos recurrentes"
        ordering = ['next_due_date']

    def __str__(self):
        return f"{self.name} ({self.amount} - {self.get_frequency_display()})"

    def clean(self):
        """Validaciones de fechas"""
        errors = {}

        if self.end_date and self.end_date < self.start_date:
            errors['end_date'] = "La fecha de fin debe ser posterior a la de inicio"

        if self.next_due_date < self.start_date:
            errors['next_due_date'] = "La próxima fecha de pago no puede ser anterior a la fecha de inicio"

        if errors:
            raise ValidationError(errors)

    def _days_in_month(self, year, month):
        """Devuelve el número de días en un mes específico"""
        if month == 12:
            return 31
        return (date(year, month + 1, 1) - date(year, month, 1)).days

    def _add_months(self, source_date, months):
        """Añade meses a una fecha manteniendo el día máximo válido"""
        year = source_date.year + (months // 12)
        month = source_date.month + (months % 12)

        if month > 12:
            month -= 12
            year += 1

        day = min(source_date.day, self._days_in_month(year, month))
        return date(year, month, day)

    def update_next_due_date(self):
        """Calcula la nueva fecha de pago según la frecuencia"""
        if self.frequency == 'monthly':
            self.next_due_date = self._add_months(self.next_due_date, 1)
        else:  # yearly
            try:
                # Intenta mantener el mismo día/mes
                self.next_due_date = self.next_due_date.replace(year=self.next_due_date.year + 1)
            except ValueError:
                # Para años bisiestos (29 de febrero)
                self.next_due_date = date(self.next_due_date.year + 1, 3, 1)

        # Desactiva si superó la fecha final
        if self.end_date and self.next_due_date > self.end_date:
            self.is_active = False

        self.save()

    def create_transaction(self):
        """Crea una transacción asociada al pago recurrente"""
        return Transaction.objects.create(
            user=self.user,
            amount=self.amount,
            category=self.category,
            date=date.today(),
            description=f"Pago recurrente: {self.name}",
            is_expense=True
        )

    def process_payment(self):
        """Ejecuta el pago si está vencido y activo"""
        if date.today() >= self.next_due_date and self.is_active:
            transaction = self.create_transaction()
            self.update_next_due_date()

            # Opcional: Crear alerta
            Alert.objects.create(
                user=self.user,
                title=f"Pago automático: {self.name}",
                message=f"Se ha procesado el pago de {self.amount}",
                alert_type='payment'
            )

            return transaction
        return None

    @classmethod
    def process_due_payments(cls):
        """Procesa todos los pagos vencidos (para el comando)"""
        return [
            payment.process_payment()
            for payment in cls.objects.filter(
                next_due_date__lte=date.today(),
                is_active=True
            ).select_related('user', 'category')
            if payment.process_payment() is not None
        ]


class Alert(models.Model):
    """Alertas para notificar al usuario (presupuesto alcanzado, pago próximo, etc.)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alerts')
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    ALERT_TYPES = [
        ('budget', 'Límite de presupuesto'),
        ('payment', 'Pago recurrente'),
        ('goal', 'Objetivo financiero'),
        ('system', 'Sistema'),
    ]
    alert_type = models.CharField(max_length=10, choices=ALERT_TYPES)

    transactions = models.ManyToManyField(Transaction, related_name='alerts')

    def get_related_transactions(self):
        return self.transactions.all().order_by('-date')

    def delete_if_empty(self):
        """Elimina la alerta si no tiene transacciones"""
        if self.transactions.count() == 0:
            self.delete()


    def __str__(self):
        return f"{self.alert_type}: {self.title}"

    class Meta:
        ordering = ['-created_at']

