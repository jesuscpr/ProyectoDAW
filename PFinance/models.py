from django.contrib.auth.models import User
from django.db import models

# Create your models here.

class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    moneda_preferida = models.CharField(max_length=3, default='EUR')  # EUR, USD, etc.
    dia_inicio_mes_financiero = models.PositiveSmallIntegerField(default=1)  # Para calcular presupuestos mensuales
    notificaciones_activas = models.BooleanField(default=True)
    presupuesto_total_mensual = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    saldo_actual = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_registro = models.DateTimeField(auto_now_add=True)


class Categoria(models.Model):
    TIPO_CHOICES = [
        ('INGRESO', 'Ingreso'),
        ('GASTO', 'Gasto'),
    ]
    nombre = models.CharField(max_length=50)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    icono = models.CharField(max_length=50, null=True, blank=True)  # Nombre del icono (FontAwesome, etc.)
    color = models.CharField(max_length=7, default="#3498db")  # Código HEX del color
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)  # Para categorías personalizadas
    es_sistema = models.BooleanField(default=False)  # Para categorías predefinidas
    activa = models.BooleanField(default=True)

    class Meta:
        unique_together = ('nombre', 'usuario')


class Transaccion(models.Model):
    TIPO_CHOICES = [
        ('INGRESO', 'Ingreso'),
        ('GASTO', 'Gasto'),
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    fecha = models.DateField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    descripcion = models.CharField(max_length=200)
    notas = models.TextField(null=True, blank=True)
    etiquetas = models.ManyToManyField('Etiqueta', blank=True)
    recurrente = models.BooleanField(default=False)


class Presupuesto(models.Model):
    PERIODO_CHOICES = [
        ('MENSUAL', 'Mensual'),
        ('SEMANAL', 'Semanal'),
        ('ANUAL', 'Anual'),
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, null=True,
                                  blank=True)  # Si es NULL, es un presupuesto general
    monto_limite = models.DecimalField(max_digits=10, decimal_places=2)
    periodo = models.CharField(max_length=10, choices=PERIODO_CHOICES, default='MENSUAL')
    fecha_inicio = models.DateField()
    activo = models.BooleanField(default=True)
    notificar_porcentaje = models.PositiveSmallIntegerField(
        default=80)  # Notificar cuando se alcance este % del presupuesto


class Recordatorio(models.Model):
    PERIODICIDAD_CHOICES = [
        ('DIARIA', 'Diaria'),
        ('SEMANAL', 'Semanal'),
        ('MENSUAL', 'Mensual'),
        ('ANUAL', 'Anual'),
        ('PERSONALIZADA', 'Personalizada'),
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField(null=True, blank=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_proxima = models.DateField()
    periodicidad = models.CharField(max_length=15, choices=PERIODICIDAD_CHOICES)
    dias_anticipacion = models.PositiveSmallIntegerField(default=3)  # Días de anticipación para notificar
    activo = models.BooleanField(default=True)


class Etiqueta(models.Model):
    nombre = models.CharField(max_length=50)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('nombre', 'usuario')


class Notificacion(models.Model):
    TIPO_CHOICES = [
        ('PRESUPUESTO', 'Límite de presupuesto'),
        ('RECORDATORIO', 'Recordatorio de pago'),
        ('SISTEMA', 'Notificación del sistema'),
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    leida = models.BooleanField(default=False)
    url_accion = models.CharField(max_length=200, null=True, blank=True)  # URL opcional para acción


class MetaFinanciera(models.Model):
    ESTADO_CHOICES = [
        ('ACTIVA', 'Activa'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(null=True, blank=True)
    monto_objetivo = models.DecimalField(max_digits=10, decimal_places=2)
    monto_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_inicio = models.DateField(auto_now_add=True)
    fecha_objetivo = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='ACTIVA')
    icono = models.CharField(max_length=50, null=True, blank=True)
    color = models.CharField(max_length=7, default="#27ae60")


class CuentaBancaria(models.Model):
    TIPO_CHOICES = [
        ('CORRIENTE', 'Cuenta Corriente'),
        ('AHORRO', 'Cuenta de Ahorro'),
        ('CREDITO', 'Tarjeta de Crédito'),
        ('EFECTIVO', 'Efectivo'),
        ('INVERSION', 'Cuenta de Inversión'),
        ('OTRO', 'Otro'),
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    saldo = models.DecimalField(max_digits=12, decimal_places=2)
    incluir_en_total = models.BooleanField(default=True)
    activa = models.BooleanField(default=True)
    color = models.CharField(max_length=7, default="#95a5a6")
    fecha_creacion = models.DateTimeField(auto_now_add=True)


class Informe(models.Model):
    TIPO_CHOICES = [
        ('MENSUAL', 'Resumen Mensual'),
        ('ANUAL', 'Resumen Anual'),
        ('CATEGORIA', 'Análisis por Categoría'),
        ('TENDENCIA', 'Análisis de Tendencias'),
        ('PERSONALIZADO', 'Informe Personalizado'),
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100)
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    configuracion = models.JSONField(null=True, blank=True)  # Para almacenar configuraciones específicas del informe

