from django.apps import AppConfig


class AdminFlowConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.admin_flow"
    verbose_name = "Admin flow"

    def ready(self):
        from django.contrib import admin

        from modules.admin_flow.site import register_module_models

        register_module_models(admin.site)
