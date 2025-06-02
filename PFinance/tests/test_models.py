from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from datetime import date, timedelta
from decimal import Decimal
from ..models import Category, UserProfile, Transaction, Budget, RecurringPayment, Alert, RecurringIncome, Goal


class CategoryModelTest(TestCase):
    def setUp(self):
        self.category_expense = Category.objects.create(
            name="Comida",
            description="Gastos en alimentación",
            is_expense=True
        )
        self.category_income = Category.objects.create(
            name="Salario",
            description="Ingresos por salario",
            is_expense=False
        )

    def test_category_creation(self):
        self.assertEqual(self.category_expense.name, "Comida")
        self.assertTrue(self.category_expense.is_expense)
        self.assertEqual(str(self.category_expense), "Comida")

    def test_income_category(self):
        self.assertEqual(self.category_income.name, "Salario")
        self.assertFalse(self.category_income.is_expense)


class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.profile = UserProfile.objects.create(
            user=self.user,
            currency='USD',
            notification_app=True
        )

    def test_profile_creation(self):
        self.assertEqual(self.profile.user.username, 'testuser')
        self.assertEqual(self.profile.currency, 'USD')
        self.assertTrue(self.profile.notification_app)
        self.assertEqual(str(self.profile), "Perfil de testuser")


class TransactionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.profile = UserProfile.objects.create(user=self.user, currency='EUR')
        self.category = Category.objects.create(name="Comida", is_expense=True)
        self.transaction = Transaction.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            category=self.category,
            is_expense=True,
            description="Supermercado"
        )

    def test_transaction_creation(self):
        self.assertEqual(self.transaction.amount, Decimal('50.00'))
        self.assertEqual(self.transaction.category.name, "Comida")
        self.assertTrue(self.transaction.is_expense)
        self.assertEqual(str(self.transaction), "Gasto: 50.00 - Comida")

    def test_income_transaction(self):
        income = Transaction.objects.create(
            user=self.user,
            amount=Decimal('1000.00'),
            category=self.category,
            is_expense=False,
            description="Salario"
        )
        self.assertFalse(income.is_expense)
        self.assertEqual(str(income), "Ingreso: 1000.00 - Comida")


class BudgetModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.profile = UserProfile.objects.create(user=self.user, currency='EUR')
        self.category = Category.objects.create(name="Comida", is_expense=True)
        self.budget = Budget.objects.create(
            user=self.user,
            category=self.category,
            amount=Decimal('300.00'),
            frequency='monthly'
        )
        Transaction.objects.create(
            user=self.user,
            category=self.category,
            amount=Decimal('100.00'),
            is_expense=True
        )

    def test_budget_creation(self):
        self.assertEqual(self.budget.amount, Decimal('300.00'))
        self.assertEqual(self.budget.frequency, 'monthly')
        self.assertEqual(str(self.budget), "Presupuesto: Comida - 300.00")

    def test_spent_amount(self):
        self.assertEqual(self.budget.spent_amount(), Decimal('100.00'))

    def test_remaining_amount(self):
        self.assertEqual(self.budget.remaining_amount(), Decimal('200.00'))


class RecurringPaymentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.profile = UserProfile.objects.create(user=self.user, currency='EUR')
        self.category = Category.objects.create(name="Servicios", is_expense=True)
        today = date.today()
        self.payment = RecurringPayment.objects.create(
            user=self.user,
            name="Netflix",
            amount=Decimal('10.99'),
            category=self.category,
            start_date=today,
            next_due_date=today,
            frequency='monthly'
        )

    def test_payment_creation(self):
        self.assertEqual(self.payment.name, "Netflix")
        self.assertEqual(self.payment.amount, Decimal('10.99'))
        self.assertTrue(self.payment.is_active)

    def test_clean_method_valid(self):
        try:
            self.payment.clean()
        except ValidationError:
            self.fail("clean() raised ValidationError unexpectedly!")

    def test_clean_method_invalid_dates(self):
        invalid_payment = RecurringPayment(
            user=self.user,
            name="Invalid",
            amount=Decimal('10.00'),
            start_date=date.today(),
            next_due_date=date.today() - timedelta(days=1),
            frequency='monthly'
        )
        with self.assertRaises(ValidationError):
            invalid_payment.clean()

    def test_update_next_due_date_monthly(self):
        original_date = self.payment.next_due_date
        self.payment.update_next_due_date()
        self.assertEqual(self.payment.next_due_date.month, original_date.month + 1 if original_date.month < 12 else 1)

    def test_process_payment(self):
        transaction = self.payment.process_payment()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.amount, Decimal('10.99'))


class AlertModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.profile = UserProfile.objects.create(user=self.user, currency='EUR')
        self.alert = Alert.objects.create(
            user=self.user,
            title="Presupuesto alcanzado",
            message="Has alcanzado el 90% de tu presupuesto de comida",
            alert_type='budget'
        )

    def test_alert_creation(self):
        self.assertEqual(self.alert.title, "Presupuesto alcanzado")
        self.assertFalse(self.alert.read)
        self.assertEqual(str(self.alert), "budget: Presupuesto alcanzado")


class RecurringIncomeModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.profile = UserProfile.objects.create(user=self.user, currency='EUR')
        self.category = Category.objects.create(name="Salario", is_expense=False)
        today = date.today()
        self.income = RecurringIncome.objects.create(
            user=self.user,
            name="Salario mensual",
            amount=Decimal('2000.00'),
            source='salary',
            category=self.category,
            start_date=today,
            next_income_date=today,
            frequency='monthly'
        )

    def test_income_creation(self):
        self.assertEqual(self.income.name, "Salario mensual")
        self.assertEqual(self.income.source, 'salary')
        self.assertTrue(self.income.is_active)

    def test_create_transaction(self):
        transaction = self.income.create_transaction()
        self.assertFalse(transaction.is_expense)
        self.assertEqual(transaction.amount, Decimal('2000.00'))


class GoalModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.profile = UserProfile.objects.create(user=self.user, currency='EUR')
        self.goal = Goal.objects.create(
            user=self.user,
            subject="Ahorro vacaciones",
            target_amount=Decimal('2000.00'),
            current_amount=Decimal('500.00')
        )

    def test_goal_creation(self):
        self.assertEqual(self.goal.subject, "Ahorro vacaciones")
        self.assertEqual(self.goal.status, 'in_progress')

    def test_progress_percentage(self):
        self.assertEqual(self.goal.progress_percentage(), 25)

    def test_complete_goal(self):
        self.goal.current_amount = Decimal('2000.00')
        self.goal.save()
        self.assertEqual(self.goal.status, 'completed')