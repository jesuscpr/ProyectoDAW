import os

import django
from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.files import File
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
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@admin.com',
        password='admin'
    )

    user1 = User.objects.create_user(
        username='juan',
        email='juan@example.com',
        password='juan',
        first_name='Juan',
        last_name='Pérez'
    )

    ruta_imagen = os.path.join(settings.BASE_DIR, 'PFinance', 'static', 'logo.png')

    with open(ruta_imagen, 'rb') as f:
        imagen = File(f)

        perfil1 = UserProfile.objects.create(
            user=user1,
            currency='EUR',
            notification_app=True,
        )
        perfil1.foto_perfil.save('logo.png', imagen, save=True)

    with open(ruta_imagen, 'rb') as f:
        imagen = File(f)

        perfil_admin = UserProfile.objects.create(
            user=admin,
            currency='EUR',
            notification_app=True,
        )
        perfil_admin.foto_perfil.save('default.jpg', imagen, save=True)

    return user1


def create_categories():
    # Categorías
    all_categories = [
        ('Nómina', 'Salario mensual', 'money-bill-wave', False),
        ('Venta', 'Venta de productos', 'shopping-bag', False),
        ('Ocio', 'Entretenimiento y diversión', 'film', True),
        ('Viajes', 'Gastos de viaje', 'plane', True),
        ('Compras', 'Compras varias', 'shopping-cart', True),
        ('Suscripción', 'Suscripciones mensuales', 'calendar-alt', True),
        ('Ingreso recurrente', 'Ingresos periódicos', 'money-bill-alt', False),
    ]

    categories = []
    for name, desc, icon, is_expense in all_categories:
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
    transactions = []

    grafica = [
        # Enero
        (Decimal('2500'), categories[0], timezone.make_aware(datetime(2025, 1, 4, 12, 0)), 'Salario', False),
        (Decimal('150'), categories[3], timezone.make_aware(datetime(2025, 1, 5, 12, 30)), 'Viaje', True),
        (Decimal('50'), categories[4], timezone.make_aware(datetime(2025, 1, 6, 16, 30)), 'Compras', True),
        (Decimal('10'), categories[5], timezone.make_aware(datetime(2025, 1, 6, 16, 30)), 'Suscripción', True),
        (Decimal('10'), categories[2], timezone.make_aware(datetime(2025, 1, 12, 19, 30)), 'Bolos', True),
        # Febrero
        (Decimal('2500'), categories[0], timezone.make_aware(datetime(2025, 2, 4, 12, 0)), 'Salario', False),
        (Decimal('75'), categories[3], timezone.make_aware(datetime(2025, 2, 15, 18, 00)), 'Viaje', True),
        (Decimal('10'), categories[5], timezone.make_aware(datetime(2025, 2, 6, 16, 30)), 'Suscripción', True),
        (Decimal('68'), categories[4], timezone.make_aware(datetime(2025, 2, 10, 18, 10)), 'Compras', True),
        (Decimal('20'), categories[2], timezone.make_aware(datetime(2025, 2, 18, 16, 0)), 'Karting', True),
        # Marzo
        (Decimal('2500'), categories[0], timezone.make_aware(datetime(2025, 3, 4, 12, 0)), 'Salario', False),
        (Decimal('115'), categories[3], timezone.make_aware(datetime(2025, 3, 25, 10, 50)), 'Viaje', True),
        (Decimal('10'), categories[5], timezone.make_aware(datetime(2025, 3, 6, 16, 30)), 'Suscripción', True),
        (Decimal('90'), categories[4], timezone.make_aware(datetime(2025, 3, 8, 20, 40)), 'Compras', True),
        (Decimal('20'), categories[2], timezone.make_aware(datetime(2025, 3, 28, 11, 0)), 'Juego', True),
        # Abril
        (Decimal('2500'), categories[0], timezone.make_aware(datetime(2025, 4, 4, 12, 0)), 'Salario', False),
        (Decimal('155'), categories[3], timezone.make_aware(datetime(2025, 4, 5, 18, 00)), 'Viaje', True),
        (Decimal('10'), categories[5], timezone.make_aware(datetime(2025, 4, 6, 16, 30)), 'Suscripción', True),
        (Decimal('20'), categories[4], timezone.make_aware(datetime(2025, 4, 15, 10, 0)), 'Compras', True),
        (Decimal('30'), categories[2], timezone.make_aware(datetime(2025, 4, 22, 15, 50)), 'Sala de juegos', True),
        # Mayo
        (Decimal('2500'), categories[0], timezone.make_aware(datetime(2025, 5, 4, 12, 0)), 'Salario', False),
        (Decimal('125'), categories[3], timezone.make_aware(datetime(2025, 5, 5, 18, 00)), 'Viaje', True),
        (Decimal('10'), categories[5], timezone.make_aware(datetime(2025, 5, 6, 16, 30)), 'Suscripción', True),
        (Decimal('13'), categories[4], timezone.make_aware(datetime(2025, 5, 10, 11, 10)), 'Compras', True),
        (Decimal('10'), categories[2], timezone.make_aware(datetime(2025, 5, 18, 18, 40)), 'Bolos', True),
        # Junio
        (Decimal('2500'), categories[0], timezone.make_aware(datetime(2025, 6, 4, 12, 0)), 'Salario', False),
        (Decimal('175'), categories[3], timezone.make_aware(datetime(2025, 6, 5, 18, 00)), 'Viaje', True),
        (Decimal('10'), categories[5], timezone.make_aware(datetime(2025, 6, 6, 16, 30)), 'Suscripción', True),
        (Decimal('50'), categories[4], timezone.make_aware(datetime(2025, 6, 9, 20, 0)), 'Compras', True),
        (Decimal('20'), categories[2], timezone.make_aware(datetime(2025, 6, 11, 17, 30)), 'Karting', True),
    ]

    for amount, category, date, desc, expense in grafica:
        transactions.append(
            Transaction.objects.create(
                user=user,
                amount=amount,
                category=category,
                date=date,
                description=desc,
                is_expense=expense
            )
        )

    return transactions


def create_budgets(user, categories):
    budgets = []

    for i, category in enumerate(categories):
        if category.is_expense:
            budgets.append(
                Budget.objects.create(
                    user=user,
                    category=category,
                    amount=Decimal(f'{(i + 1) * 20:.2f}'),
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
        ('Netflix', Decimal('12.99'), categories[5]),
        ('Gimnasio', Decimal('35.00'), categories[5]),
        ('Spotify', Decimal('9.99'), categories[5]),
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
        ('Nuevo portátil', Decimal('2500.00'), Decimal('1200.00'), 'MacBook Pro'),
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