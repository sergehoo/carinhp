from django.apps import AppConfig


class RageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rage'

    def ready(self):
        import rage_INHP.signals
