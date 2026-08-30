from django.apps import AppConfig


class BackofficeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.backoffice"
    verbose_name = "backoffice"

    def ready(self):
        from modules.backoffice import signals  # noqa: F401
