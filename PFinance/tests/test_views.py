from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, RequestFactory, override_settings
from django.urls import reverse
from datetime import date
from decimal import Decimal
from PFinance.views import *


class LandingPageViewTest(TestCase):
    def test_landing_page_unauthenticated(self):
        response = self.client.get(reverse('pfinance:landing'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pfinance/landing.html')
        self.assertContains(response, 'Registro de transacciones')

    def test_landing_page_authenticated_redirect(self):
        user = User.objects.create_user(username='testuser', password='12345')
        self.profile = UserProfile.objects.create(user=user, currency='EUR')
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('pfinance:landing'))
        self.assertRedirects(response, reverse('pfinance:dashboard'))


class DashboardViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.profile = UserProfile.objects.create(user=self.user, currency='EUR')
        self.category = Category.objects.create(name='Comida', is_expense=True)

        # Crear datos de prueba
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            category=self.category,
            is_expense=True,
            date=timezone.now()
        )
        Budget.objects.create(
            user=self.user,
            category=self.category,
            amount=Decimal('300.00'),
            frequency='monthly'
        )
        Goal.objects.create(
            user=self.user,
            subject='Ahorro vacaciones',
            target_amount=Decimal('2000.00'),
            current_amount=Decimal('500.00')
        )

    def test_dashboard_authenticated(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('pfinance:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pfinance/dashboard.html')

        # Verificar que los datos básicos están en el contexto
        self.assertIn('categories_labels', response.context)
        self.assertIn('months_labels', response.context)
        self.assertIn('goals_data', response.context)

    def test_get_category_expenses(self):
        view = DashboardView()
        request = self.factory.get('/')
        request.user = self.user
        view.request = request

        data = view.get_category_expenses(self.user)
        self.assertEqual(len(data['labels']), 1)
        self.assertEqual(data['labels'][0], 'Comida')
        self.assertEqual(data['values'][0], 50.0)

    def test_get_monthly_summary(self):
        view = DashboardView()
        request = self.factory.get('/')
        request.user = self.user
        view.request = request

        data = view.get_monthly_summary(self.user)
        self.assertEqual(len(data['labels']), 6)
        self.assertGreater(data['expenses'][-1], 0)  # El último mes debería tener gastos


class SignUpViewTest(TestCase):
    def test_signup_get(self):
        response = self.client.get(reverse('pfinance:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')

    def test_signup_post_success(self):
        data = {
            'username': 'newuser',
            'email': 'test@tests.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
            'currency': 'USD'
        }
        response = self.client.post(reverse('pfinance:register'), data)
        self.assertEqual(response.status_code, 302)  # Redirección después de registro
        self.assertTrue(User.objects.filter(username='newuser').exists())


class ProfileViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        test_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'simple image content',  # Contenido binario simulado
            content_type='image/jpeg'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            currency='EUR',
            foto_perfil=test_image
        )

    def test_profile_view_authenticated(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('pfinance:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pfinance/profile_detail.html')
        self.assertEqual(response.context['profile'], self.profile)


@override_settings(CSRF_COOKIE_SECURE=False, CSRF_COOKIE_HTTPONLY=False)
class ProfileUpdateViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345', email='test@tests.com')
        self.profile = UserProfile.objects.create(user=self.user, currency='EUR')

    def test_profile_update_get(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('pfinance:profile_edit'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pfinance/profile_edit.html')

    def test_profile_update_post(self):
        self.client.login(username='testuser', password='12345')
        data = {
            'email': 'test@tests.com',
            'currency': 'USD',
            'notification_app': 'on'
        }
        response = self.client.post(reverse('pfinance:profile_edit'), data)

        self.assertEqual(response.status_code, 302)  # Redirección después de actualizar
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.currency, 'USD')


class TransactionListViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.profile = UserProfile.objects.create(user=self.user, currency='EUR')
        self.category = Category.objects.create(name='Comida', is_expense=True)
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            category=self.category,
            is_expense=True
        )

    def test_transaction_list_authenticated(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('pfinance:transactions_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pfinance/transactions_list.html')
        self.assertEqual(len(response.context['transactions']), 1)

    def test_transaction_list_filter_expenses(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('pfinance:transactions_list') + '?type=expense')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['transactions']), 1)

    def test_transaction_list_filter_income(self):
        # Crear una transacción de ingreso
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('1000.00'),
            category=self.category,
            is_expense=False
        )

        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('pfinance:transactions_list') + '?type=income')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['transactions']), 1)
        self.assertFalse(response.context['transactions'][0].is_expense)


class TransactionCreateViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.profile = UserProfile.objects.create(user=self.user, currency='EUR')
        self.category = Category.objects.create(name='Comida', is_expense=True)

    def test_transaction_create_get(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('pfinance:transactions_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pfinance/transactions_create.html')

    def test_transaction_create_post(self):
        self.client.login(username='testuser', password='12345')
        data = {
            'amount': '75.50',
            'category': self.category.id,
            'is_expense': True,
            'date': timezone.now().strftime('%Y-%m-%d'),
            'description': 'Cena'
        }
        response = self.client.post(reverse('pfinance:transactions_create'), data)
        self.assertEqual(response.status_code, 302)  # Redirección después de creación
        self.assertEqual(Transaction.objects.count(), 1)


class BudgetListViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.profile = UserProfile.objects.create(user=self.user, currency='EUR')
        self.category = Category.objects.create(name='Comida', is_expense=True)
        Budget.objects.create(
            user=self.user,
            category=self.category,
            amount=Decimal('300.00'),
            frequency='monthly'
        )

    def test_budget_list_authenticated(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('pfinance:budgets_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pfinance/budgets_list.html')
        self.assertEqual(len(response.context['budgets']), 1)


class BudgetCreateViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.profile = UserProfile.objects.create(user=self.user, currency='EUR')
        self.category = Category.objects.create(name='Comida', is_expense=True)

    def test_budget_create_get(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('pfinance:budgets_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pfinance/budgets_create.html')

    def test_budget_create_post(self):
        self.client.login(username='testuser', password='12345')
        data = {
            'category': self.category.id,
            'amount': '300.00',
            'frequency': 'monthly'
        }
        response = self.client.post(reverse('pfinance:budgets_create'), data)
        self.assertEqual(response.status_code, 302)  # Redirección después de creación
        self.assertEqual(Budget.objects.count(), 1)


class RecurringPaymentListViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.profile = UserProfile.objects.create(user=self.user, currency='EUR')
        self.category = Category.objects.create(name='Servicios', is_expense=True)
        RecurringPayment.objects.create(
            user=self.user,
            name='Netflix',
            amount=Decimal('10.99'),
            category=self.category,
            start_date=date.today(),
            next_due_date=date.today(),
            frequency='monthly'
        )

    def test_recurring_payment_list(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('pfinance:recurring_payments'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pfinance/recurring_payments_list.html')
        self.assertEqual(len(response.context['payments']), 1)


class GoalListViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.profile = UserProfile.objects.create(user=self.user, currency='EUR')
        Goal.objects.create(
            user=self.user,
            subject='Ahorro vacaciones',
            target_amount=Decimal('2000.00'),
            current_amount=Decimal('500.00')
        )

    def test_goal_list(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('pfinance:goals_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pfinance/goal_list.html')
        self.assertEqual(len(response.context['goals']), 1)


class GoalCreateViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.profile = UserProfile.objects.create(user=self.user, currency='EUR')

    def test_goal_create_get(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('pfinance:goals_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pfinance/goal_create.html')

    def test_goal_create_post(self):
        self.client.login(username='testuser', password='12345')
        data = {
            'subject': 'Nuevo coche',
            'target_amount': '15000.00',
            'current_amount': '2000.00'
        }
        response = self.client.post(reverse('pfinance:goals_create'), data)
        self.assertEqual(response.status_code, 302)  # Redirección después de creación
        self.assertEqual(Goal.objects.count(), 1)


class AlertListViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.profile = UserProfile.objects.create(user=self.user, currency='EUR')
        Alert.objects.create(
            user=self.user,
            title='Presupuesto alcanzado',
            message='Has alcanzado el 90% de tu presupuesto',
            alert_type='budget'
        )

    def test_alert_list(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('pfinance:alerts'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pfinance/alerts_list.html')
        self.assertEqual(len(response.context['alerts']), 1)