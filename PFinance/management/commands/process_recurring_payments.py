from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from PFinance.models import RecurringPayment, Alert


class Command(BaseCommand):
    help = 'Procesa pagos recurrentes vencidos y crea alertas de recordatorio'

    def handle(self, *args, **options):
        today = timezone.now().date()

        self.stdout.write(f"\nIniciando procesamiento de pagos recurrentes ({today})...")

        # 1. Procesar pagos vencidos
        self._process_due_payments(today)

        # 2. Crear alertas de recordatorio (una sola vez)
        self._create_one_time_reminders(today)

    def _process_due_payments(self, today):
        """Procesa pagos cuya fecha de pago ya llegó"""
        payments = RecurringPayment.objects.filter(
            next_due_date__lte=today,
            is_active=True
        ).select_related('user', 'category')

        if not payments.exists():
            self.stdout.write(self.style.SUCCESS("No hay pagos pendientes para procesar"))
            return

        self.stdout.write(f"\n💸 Procesando pagos vencidos ({payments.count()}):")

        success_count = 0
        for payment in payments:
            try:
                transaction = payment.process_payment()
                if transaction:
                    self.stdout.write(
                        f"✔️ Transacción #{transaction.id} para {payment.name} "
                        f"(Monto: {payment.amount}, Próximo pago: {payment.next_due_date})"
                    )
                    success_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error con {payment.name}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f"Transacciones creadas: {success_count}"))

    def _create_one_time_reminders(self, today):
        """Crea alertas de recordatorio UNA SOLA VEZ cuando hoy = next_due_date - reminder_days"""
        upcoming_payments = RecurringPayment.objects.filter(
            next_due_date__gt=today,  # Solo pagos futuros
            is_active=True
        ).select_related('user')

        alert_count = 0
        self.stdout.write(f"\n🔔 Buscando pagos para recordatorio (reminder_days):")

        for payment in upcoming_payments:
            reminder_date = payment.next_due_date - timedelta(days=payment.reminder_days)

            if today == reminder_date:
                try:
                    Alert.objects.create(
                        user=payment.user,
                        title=f"Recordatorio de pago: {payment.name}",
                        message=(
                            f"Se cobrarán {payment.amount} el {payment.next_due_date}. "
                            f"Frecuencia: {payment.get_frequency_display()}"
                        ),
                        alert_type='payment'
                    )
                    self.stdout.write(
                        f"✉️ Alerta creada para {payment.name} "
                        f"(Vence: {payment.next_due_date}, "
                        f"Recordatorio configurado: {payment.reminder_days} días antes)"
                    )
                    alert_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Error al crear alerta para {payment.name}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f"Alertas creadas: {alert_count}"))
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("✅ Proceso completado")
        self.stdout.write("=" * 50)