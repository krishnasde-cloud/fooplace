from django.apps import AppConfig


class ClerkConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.clerk"
    verbose_name = "Clerk"
    api_prefix = "me"
