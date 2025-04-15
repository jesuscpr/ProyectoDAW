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


class UserProfile(models.Model):
    """Perfil extendido del usuario con información financiera adicional"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    monthly_income = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='EUR')
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budgets')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)  # Null significa presupuesto recurrente
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Presupuesto: {self.category.name} - {self.amount}"


class RecurringPayment(models.Model):
    """Pagos recurrentes programados (suscripciones, facturas, etc.)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recurring_payments')
    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # Null significa indefinido

    FREQUENCY_CHOICES = [
        ('daily', 'Diario'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
        ('yearly', 'Anual'),
    ]
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='monthly')
    next_due_date = models.DateField()
    reminder_days = models.PositiveSmallIntegerField(default=3)  # Días antes para recordatorio

    def __str__(self):
        return f"{self.name} ({self.amount} - {self.get_frequency_display()})"


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

    def __str__(self):
        return f"{self.alert_type}: {self.title}"

    class Meta:
        ordering = ['-created_at']