from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, CURRENCY_CHOICES
from django.utils.translation import gettext_lazy as _

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