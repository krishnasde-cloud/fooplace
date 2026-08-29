"""Limit Django admin to Fooplace admin users and register app data."""

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.models import User as AuthUser


class StaffModelAdmin:
    """Skip LogEntry writes — request.user is a Clerk session, not AUTH_USER_MODEL."""

    def log_addition(self, *args, **kwargs):
        return None

    def log_change(self, *args, **kwargs):
        return None

    def log_deletion(self, *args, **kwargs):
        return None

    def log_deletions(self, *args, **kwargs):
        return None

    def log_actions(self, *args, **kwargs):
        return None


def is_admin_user(user) -> bool:
    record = getattr(user, "record", None)
    return bool(record is not None and record.is_active and record.is_admin)


def configure_admin_site(site) -> None:
    if getattr(site, "_admin_flow_configured", False):
        return
    site._admin_flow_configured = True
    site.site_header = "Fooplace admin"
    site.site_title = "Fooplace admin"
    site.index_title = "All data"
    site.login_template = "admin_flow/login.html"
    site.index_template = "admin_flow/index.html"

    original_login = site.login

    def has_permission(request):
        return is_admin_user(request.user)

    def login(request, extra_context=None):
        extra_context = {
            **(extra_context or {}),
            "clerk_publishable_key": settings.CLERK_PUBLISHABLE_KEY,
            "signed_in": request.user.is_authenticated,
            "is_admin": is_admin_user(request.user),
        }
        return original_login(request, extra_context=extra_context)

    site.has_permission = has_permission
    site.login = login

    for model in (AuthUser, Group):
        if site.is_registered(model):
            site.unregister(model)


def register_module_models(site) -> None:
    from django.contrib import admin

    class AutoModelAdmin(StaffModelAdmin, admin.ModelAdmin):
        pass

    for model in apps.get_models():
        app_name = model._meta.app_config.name
        if not app_name.startswith("modules."):
            continue
        if site.is_registered(model):
            continue
        site.register(model, AutoModelAdmin)
