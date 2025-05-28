from django.db.models import Sum
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import Transaction, Budget, RecurringPayment, Alert, Goal, RecurringIncome
from datetime import timedelta
from decimal import Decimal



# Alertas para presupuestos cuando se guarda una transaccion
@receiver(post_save, sender=Transaction)
def create_budget_alert(sender, instance, created, **kwargs):
    """
    Crea alertas considerando el período del presupuesto (mensual/anual)
    y vincula las transacciones correspondientes.
    """
    notifications = instance.user.profile.notification_app

    if not created or not instance.is_expense:
        return

    try:
        budget = Budget.objects.select_related('user__profile').get(
            user=instance.user,
            category=instance.category,
            is_active=True
        )
    except Budget.DoesNotExist:
        return

    # Determinamos el rango de fechas según la frecuencia del presupuesto
    now = timezone.now()
    if budget.frequency == 'yearly':
        # Presupuesto anual: consideramos el año completo
        date_filter = {
            'date__year': now.year
        }
        period_description = f"del año {now.year}"
    else:
        # Presupuesto mensual (default)
        date_filter = {
            'date__year': now.year,
            'date__month': now.month
        }
        period_description = f"del mes {now.month}/{now.year}"

    # Calculamos el total gastado en el período correspondiente
    transactions = Transaction.objects.filter(
        user=instance.user,
        category=instance.category,
        is_expense=True,
        **date_filter
    )

    spent = transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    threshold = budget.amount * Decimal('0.9')

    # Verificamos si supera el 90% del presupuesto
    if spent < threshold:
        return

    # Verificamos si supera el 100% del presupuesto
    if spent > budget.amount:
        if notifications:
            alert, created = Alert.objects.get_or_create(
                user=instance.user,
                alert_type='budget',
                title=f"Presupuesto traspasa el límite: {budget.category.name}",
                defaults={
                    'message': (
                        f"Has gastado {spent:.2f}{budget.user.profile.currency} "
                        f"({(spent / budget.amount) * 100:.1f}%) "
                        f"del presupuesto {period_description}"
                    )
                }
            )
        budget.state = 'overlimit'
        budget.save()
    else:
        # Buscamos o creamos la alerta
        if notifications:
            alert, created = Alert.objects.get_or_create(
                user=instance.user,
                alert_type='budget',
                title=f"Presupuesto al límite: {budget.category.name}",
                defaults={
                    'message': (
                        f"Has gastado {spent:.2f}{budget.user.profile.currency} "
                        f"({(spent / budget.amount) * 100:.1f}%) "
                        f"del presupuesto {period_description}"
                    )
                }
            )
        budget.state = 'limit'
        budget.save()

    # Vinculamos TODAS las transacciones del período
    if notifications:
        if created:
            alert.transactions.set(transactions)
        else:
            # Actualizamos transacciones si la alerta ya existía
            current_transactions = set(alert.transactions.all())
            new_transactions = set(transactions) - current_transactions
            if new_transactions:
                alert.transactions.add(*new_transactions)


# Alertas para pagos recurrentes
@receiver(post_save, sender=RecurringPayment)
def check_recurring_payment_alerts(sender, instance, **kwargs):
    notifications = instance.user.profile.notification_app
    if notifications:
        if instance.next_due_date <= timezone.now().date() + timedelta(days=instance.reminder_days):
            Alert.objects.get_or_create(
                user=instance.user,
                title=f"Pago próximo: {instance.name}",
                message=f"Se cobrarán {instance.amount:.2f} {instance.user.profile.currency} el {instance.next_due_date.strftime('%d/%m/%Y')}",
                alert_type='payment',
                defaults={'read': False}
            )


# Alertas para metas
@receiver(post_save, sender=Goal)
def check_goal_completion(sender, instance, created, **kwargs):
    """
    Signal que verifica si se alcanzó el objetivo y crea una alerta.
    """
    notifications = instance.user.profile.notification_app

    if notifications:
        if not created:  # Solo para actualizaciones (no creación inicial)
            if instance.current_amount >= instance.target_amount and instance.status == 'completed':
                # Verificar si ya existe una alerta para evitar duplicados
                existing_alert = Alert.objects.filter(
                    user=instance.user,
                    alert_type='goal',
                    title=f"Meta alcanzada: {instance.subject}"
                ).exists()

                if not existing_alert:
                    Alert.objects.create(
                        user=instance.user,
                        title=f"Meta alcanzada: {instance.subject}",
                        message=f"¡Felicidades! Has alcanzado tu meta de {instance.target_amount} {instance.user.profile.currency} para '{instance.subject}'.",
                        alert_type='goal'
                    )


# Modificación de estado de presupuesto y borrado de alerta al borrar una transacción
@receiver(post_delete, sender=Transaction)
def update_budget_on_transaction_delete(sender, instance, **kwargs):
    """
    Actualiza el estado del presupuesto cuando se borra una transacción,
    revirtiendo los cambios si ya no se cumplen las condiciones.
    """
    if not instance.is_expense:
        return

    try:
        budget = Budget.objects.select_related('user__profile').get(
            user=instance.user,
            category=instance.category,
            is_active=True
        )
    except Budget.DoesNotExist:
        return

    # Determinamos el rango de fechas según la frecuencia del presupuesto
    now = timezone.now()
    if budget.frequency == 'yearly':
        date_filter = {
            'date__year': now.year
        }
    else:
        date_filter = {
            'date__year': now.year,
            'date__month': now.month
        }

    # Obtenemos transacciones actuales del período
    transactions = Transaction.objects.filter(
        user=instance.user,
        category=instance.category,
        is_expense=True,
        **date_filter
    )

    # Calculamos el nuevo total gastado
    spent = transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    threshold = budget.amount * Decimal('0.9')

    # Buscamos alertas existentes para este presupuesto
    alert = Alert.objects.filter(
        user=instance.user,
        alert_type='budget',
        title__contains=budget.category.name
    ).first()

    # Lógica para actualizar el estado del presupuesto
    if spent > budget.amount:
        # Mantenemos estado overlimit si aún se supera el 100%
        budget.state = 'overlimit'
        if alert and 'traspasa' not in alert.title:
            alert.title = f"Presupuesto traspasa el límite: {budget.category.name}"
            alert.save()
    elif spent > threshold:
        # Si está entre 90-100%, cambiamos a limit (si estaba en overlimit)
        budget.state = 'limit'
        if alert and 'traspasa' in alert.title:
            alert.delete()
    else:
        # Si está por debajo del 90%, volvemos a ok
        budget.state = 'ok'
        # Eliminamos la alerta si ya no es necesaria
        if alert:
            alert.delete()

    budget.save()


# Alertas para ingresos recurrentes
@receiver(post_save, sender=RecurringIncome)
def check_recurring_income_alerts(sender, instance, **kwargs):
    notifications = instance.user.profile.notification_app
    if notifications:
        if instance.next_income_date <= timezone.now().date() + timedelta(days=3):
            Alert.objects.get_or_create(
                user=instance.user,
                title=f"Ingreso próximo: {instance.name}",
                message=f"Se cobrarán {instance.amount:.2f} {instance.user.profile.currency} el {instance.next_income_date.strftime('%d/%m/%Y')}",
                alert_type='payment',
                defaults={'read': False}
            )

