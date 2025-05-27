from celery import shared_task
from django.core.management import call_command

@shared_task
def process_recurring_payments():
    call_command('process_recurring_payments')


@shared_task
def process_recurring_incomes():
    call_command('process_recurring_incomes')



