from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import UserProfile, CURRENCY_CHOICES, Category, Budget, Transaction, RecurringPayment, RecurringIncome, \
    Goal


# Formulario para el registro
class SignUpForm(UserCreationForm):
    monthly_income = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        initial=0.00,
        label="Ingreso mensual",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    currency = forms.ChoiceField(
        choices=CURRENCY_CHOICES,
        initial='EUR',
        label="Moneda",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    notification_app = forms.BooleanField(
        initial=True,
        required=False,
        label="Recibir notificaciones en la app",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].label = "Contraseña"
        self.fields['password2'].label = "Confirmar contraseña"
        self.fields['password1'].help_text = "Mínimo 8 caracteres. No puede ser similar a tu información personal."
        self.fields['password2'].help_text = "Repite la contraseña para verificación."
        self.fields['email'].label = "Correo electrónico"

    def save(self, commit=True):
        user = super().save(commit=commit)

        UserProfile.objects.create(
            user=user,
            monthly_income=self.cleaned_data['monthly_income'],
            currency=self.cleaned_data['currency'],
            notification_app=self.cleaned_data['notification_app']
        )

        return user


# Formulario para editar el perfil
class ProfileEditForm(forms.ModelForm):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = UserProfile
        fields = ['email', 'monthly_income', 'currency', 'notification_app']
        labels = {
            'email': 'Correo electrónico',
            'monthly_income': 'Ingreso mensual',
            'currency': 'Moneda',
            'notification_app': 'Recibir notificaciones en la app'
        }
        widgets = {
            'monthly_income': forms.NumberInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'notification_app': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].label = "Correo electrónico"
        self.fields['monthly_income'].label = 'Ingreso mensual'
        self.fields['currency'].label = 'Moneda'
        self.fields['notification_app'].label = 'Recibir notificaciones en la app'
        if self.instance and hasattr(self.instance, 'user'):
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.email = self.cleaned_data['email']

        if commit:
            try:
                with transaction.atomic():
                    user.save()
                    profile.save()
            except Exception as e:
                raise ValidationError(f"Error al guardar: {str(e)}")

        return profile

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(pk=self.instance.user.pk).exists():
            raise forms.ValidationError("Ya existe un usuario con ese email")
        return email

    def clean_monthly_income(self):
        income = self.cleaned_data.get('monthly_income')
        if income and income < 0:
            raise forms.ValidationError("El ingreso no puede ser negativo")
        return income


# Formulario para presupuestos
class BudgetForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        self.user = user  # Guardamos el usuario como atributo del formulario
        super().__init__(*args, **kwargs)
        if user:
            self.fields['category'].queryset = Category.objects.all()

    class Meta:
        model = Budget
        fields = ['category', 'amount', 'frequency', 'is_active']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '1.00',
                'min': '1.00'
            }),
            'frequency': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'category': 'Categoría',
            'amount': 'Monto presupuestado',
            'frequency': 'Frecuencia',
            'is_active': 'Presupuesto activo'
        }

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        frequency = cleaned_data.get('frequency')

        user = getattr(self.instance, 'user', None) or self.user

        if category and frequency and user:
            # Verificar si ya existe un presupuesto para esta categoría y frecuencia
            queryset = Budget.objects.filter(
                user=user,
                category=category,
                frequency=frequency
            )
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise forms.ValidationError(
                    f"Ya existe un presupuesto {frequency.lower()} para esta categoría"
                )

        return cleaned_data


# Formulario para transacciones
class TransactionForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['category'].queryset = Category.objects.all()

        # Configurar el campo de fecha
        self.fields['date'].widget = forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control',
                'max': timezone.now().strftime('%Y-%m-%dT%H:%M')
            },
            format='%Y-%m-%dT%H:%M'
        )
        self.fields['date'].initial = timezone.now()

    class Meta:
        model = Transaction
        fields = ['amount', 'category', 'date', 'description', 'is_expense']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'is_expense': forms.RadioSelect(choices=[(True, 'Gasto'), (False, 'Ingreso')])
        }
        labels = {
            'amount': 'Monto',
            'category': 'Categoría',
            'date': 'Fecha y hora',
            'description': 'Asunto',
            'is_expense': 'Tipo de transacción'
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("El monto debe ser mayor a cero")
        return amount


# Formulario para pagos recurrentes
class RecurringPaymentForm(forms.ModelForm):
    class Meta:
        model = RecurringPayment
        fields = ['name', 'amount', 'category', 'start_date',
                  'end_date', 'frequency', 'next_due_date', 'reminder_days']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'next_due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        next_due_date = cleaned_data.get('next_due_date')

        if end_date and start_date and end_date < start_date:
            raise ValidationError("La fecha de fin debe ser posterior a la de inicio")


        if next_due_date < start_date:
            raise ValidationError("La próxima fecha de pago no puede ser anterior a la fecha de inicio")

        return cleaned_data


# Formulario para ingresos recurrentes
class RecurringIncomeForm(forms.ModelForm):
    class Meta:
        model = RecurringIncome
        fields = ['name', 'amount', 'source', 'category', 'start_date',
                  'end_date', 'frequency', 'next_income_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'next_income_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user:
            self.fields['category'].queryset = Category.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        next_date = cleaned_data.get('next_income_date')

        if end_date and start_date and end_date < start_date:
            raise ValidationError("La fecha de fin debe ser posterior a la de inicio")

        if next_date and start_date and next_date < start_date:
            raise ValidationError("La próxima fecha de ingreso no puede ser anterior a la fecha de inicio")


class GoalForm(forms.ModelForm):
    """Formulario base para crear/editar metas (no usado en la actualización de cantidad)"""

    class Meta:
        model = Goal
        fields = ['subject', 'target_amount', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['target_amount'].widget.attrs.update({
            'step': '1.00',
            'min': '1.00'
        })


class GoalAmountUpdateForm(forms.ModelForm):
    """Formulario exclusivo para actualizar el monto acumulado"""

    class Meta:
        model = Goal
        fields = ['current_amount']
        labels = {
            'current_amount': 'Monto actual'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['current_amount'].widget = forms.NumberInput(attrs={
            'step': '1.00',
            'min': '0',
            'class': 'form-control form-control-lg',
            'placeholder': 'Ingrese el nuevo valor'
        })

        # Establecer máximo como el target_amount + margen
        if self.instance and self.instance.target_amount:
            self.fields['current_amount'].widget.attrs['max'] = \
                str(float(self.instance.target_amount) + 10000)

    def clean_current_amount(self):
        current_amount = self.cleaned_data['current_amount']

        if current_amount < 0:
            raise forms.ValidationError("El monto no puede ser negativo")

        # Validación opcional para no superar demasiado el objetivo
        target = self.instance.target_amount
        limit = float(target) * 1.5
        currency = self.instance.user.profile.currency
        if target and current_amount > float(target) * 1.5:  # 50% más del objetivo
            raise forms.ValidationError(
                f"El monto actual no puede superar en más del 50% el objetivo. ({limit:.2f} {currency}))"
            )

        return current_amount

