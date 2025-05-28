from django.core.management.base import BaseCommand
from django.utils import timezone
from PFinance.models import RecurringIncome, Alert, UserProfile
from datetime import timedelta


class Command(BaseCommand):
    help = 'Procesa ingresos recurrentes vencidos y crea transacciones'

    def handle(self, *args, **options):
        today = timezone.now().date()

        self.stdout.write(f"\nProcesando ingresos recurrentes ({today})")

        # Procesar ingresos vencidos
        incomes = RecurringIncome.objects.filter(
            next_income_date__lte=today,
            is_active=True
        ).select_related('user', 'category')

        success_count = 0
        for income in incomes:
            try:
                transaction = income.process_income()
                if transaction:
                    self.stdout.write(
                        f"Ingreso creado: {income.name} "
                        f"(Monto: {income.amount}{income.user.profile.currency}, "
                        f"Próximo: {income.next_income_date})"
                    )
                    success_count += 1

                    # Crear alerta
                    Alert.objects.create(
                        user=income.user,
                        title=f"Ingreso registrado: {income.name}",
                        message=f"Se ha ingresado {income.amount} {income.user.profile.currency} ({income.get_source_display()})",
                        alert_type='income'
                    )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error con {income.name}: {str(e)}"))

        # Alertas anticipadas
        upcoming_incomes = RecurringIncome.objects.filter(
            next_income_date__gt=today,
            is_active=True
        )

        reminder_count = 0
        for income in upcoming_incomes:
            reminder_date = income.next_income_date - timedelta(days=3)  # 3 días antes
            if today == reminder_date:
                Alert.objects.create(
                    user=income.user,
                    title=f"Recordatorio de ingreso: {income.name}",
                    message=f"Esperado el {income.next_income_date}",
                    alert_type='reminder'
                )
                reminder_count += 1

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(f"Ingresos procesados: {success_count}")
        self.stdout.write(f"Recordatorios creados: {reminder_count}")
        self.stdout.write("=" * 50)