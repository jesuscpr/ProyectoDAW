# populate_db.py
import os
import django
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ProyectoDAW.settings')
django.setup()

from django.contrib.auth.models import User
from PFinance.models import (
    Category, UserProfile, Transaction, Budget,
    RecurringPayment, Alert, RecurringIncome, Goal
)


def create_users():
    # Crear usuarios
    user1 = User.objects.create_user(
        username='juan',
        email='juan@example.com',
        password='juan',
        first_name='Juan',
        last_name='Pérez'
    )

    # Crear perfiles de usuario
    UserProfile.objects.create(user=user1, currency='EUR', notification_app=True)

    return user1


def create_categories():
    # Categorías de gastos (is_expense=True)
    expense_categories = [
        ('Nómina', 'Salario mensual', 'money-bill-wave', False),
        ('Venta', 'Venta de productos', 'shopping-bag', False),
        ('Ocio', 'Entretenimiento y diversión', 'film', True),
        ('Viajes', 'Gastos de viaje', 'plane', True),
        ('Compras', 'Compras varias', 'shopping-cart', True),
        ('Suscripción', 'Suscripciones mensuales', 'calendar-alt', True),
        ('Ingreso recurrente', 'Ingresos periódicos', 'money-bill-alt', False),
    ]

    categories = []
    for name, desc, icon, is_expense in expense_categories:
        categories.append(
            Category.objects.create(
                name=name,
                description=desc,
                icon=icon,
                is_expense=is_expense
            )
        )

    return categories


def create_transactions(user, categories):
    today = timezone.now()
    transactions = []

    cat_gasto = [cat for cat in categories if cat.is_expense]

    # Gastos
    for i in range(1, 31):
        trans_date = today - timedelta(days=i)
        amount = Decimal(f'{i * 5.50:.2f}')

        transactions.append(
            Transaction.objects.create(
                user=user,
                amount=amount,
                category=cat_gasto[i % len(cat_gasto)],
                date=trans_date,
                description=f'Transacción #{i}',
                is_expense=True
            )
        )

    # Ingresos
    for i in range(1, 6):
        trans_date = today - timedelta(days=i * 7)
        amount = Decimal('1200.00')

        transactions.append(
            Transaction.objects.create(
                user=user,
                amount=amount,
                category=categories[0],  # Nómina
                date=trans_date,
                description='Salario mensual',
                is_expense=False
            )
        )

    return transactions


def create_budgets(user, categories):
    budgets = []

    for i, category in enumerate(categories):
        if category.is_expense:  # Solo presupuestos para gastos
            budgets.append(
                Budget.objects.create(
                    user=user,
                    category=category,
                    amount=Decimal(f'{(i + 1) * 200:.2f}'),
                    frequency='monthly',
                    is_active=True
                )
            )

    return budgets


def create_recurring_payments(user, categories):
    today = timezone.now().date()
    payments = []

    # Suscripciones
    services = [
        ('Netflix', Decimal('12.99'), categories[5]),  # Suscripción
        ('Gimnasio', Decimal('35.00'), categories[5]),  # Suscripción
        ('Spotify', Decimal('9.99'), categories[5]),  # Suscripción
    ]

    for name, amount, category in services:
        payments.append(
            RecurringPayment.objects.create(
                user=user,
                name=name,
                amount=amount,
                category=category,
                start_date=today - timedelta(days=90),
                end_date=today + timedelta(days=365),
                frequency='monthly',
                next_due_date=today + timedelta(days=7),
                reminder_days=3,
                is_active=True
            )
        )

    return payments


def create_recurring_incomes(user, categories):
    today = timezone.now().date()
    incomes = []

    # Ingresos recurrentes
    income_sources = [
        ('Salario', Decimal('2500.00'), 'salary', categories[0]),  # Nómina
        ('Alquiler', Decimal('800.00'), 'rental', categories[6]),  # Ingreso recurrente
        ('Inversiones', Decimal('150.00'), 'investment', None),
    ]

    for name, amount, source, category in income_sources:
        incomes.append(
            RecurringIncome.objects.create(
                user=user,
                name=name,
                amount=amount,
                source=source,
                category=category,
                start_date=today - timedelta(days=180),
                end_date=today + timedelta(days=365),
                frequency='monthly',
                next_income_date=today + timedelta(days=15),
                is_active=True
            )
        )

    return incomes


def create_goals(user):
    goals = []

    goal_data = [
        ('Viaje a Japón', Decimal('5000.00'), Decimal('1200.00'), 'Ahorrar para viaje'),
        ('Nuevo portátil', Decimal('1200.00'), Decimal('800.00'), 'MacBook Pro'),
        ('Fondo de emergencia', Decimal('10000.00'), Decimal('3500.00'), '6 meses de gastos'),
    ]

    for subject, target, current, notes in goal_data:
        goals.append(
            Goal.objects.create(
                user=user,
                subject=subject,
                target_amount=target,
                current_amount=current,
                notes=notes,
                status='in_progress' if current < target else 'completed'
            )
        )

    return goals


def main():
    print("Creando datos de prueba...")

    # Limpiar base de datos existente
    print("Limpiando datos existentes...")
    models = [Category, Transaction, Budget,
              RecurringPayment, Alert, RecurringIncome, Goal]

    for model in models:
        model.objects.all().delete()

    UserProfile.objects.exclude(user__is_superuser=True).delete()

    User.objects.exclude(username='admin').delete()

    # Crear datos
    user1 = create_users()
    categories = create_categories()
    budgets = create_budgets(user1, categories)
    transactions = create_transactions(user1, categories)
    payments = create_recurring_payments(user1, categories)
    incomes = create_recurring_incomes(user1, categories)
    goals = create_goals(user1)

    print("¡Datos de prueba creados exitosamente!")
    print(f"- Usuarios: 1 (juan)")
    print(f"- Categorías: {len(categories)}")
    print(f"- Transacciones: {len(transactions)}")
    print(f"- Presupuestos: {len(budgets)}")
    print(f"- Pagos recurrentes: {len(payments)}")
    print(f"- Ingresos recurrentes: {len(incomes)}")
    print(f"- Metas: {len(goals)}")


if __name__ == '__main__':
    main()