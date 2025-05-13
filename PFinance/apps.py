from django.apps import AppConfig


class PfinanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'PFinance'

    def ready(self):
        import PFinance.signals
