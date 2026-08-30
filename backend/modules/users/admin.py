from django.contrib import admin

from modules.admin_flow.site import StaffModelAdmin
from modules.users.models import User


@admin.register(User)
class UserAdmin(StaffModelAdmin, admin.ModelAdmin):
    list_display = (
        "user_id",
        "name",
        "email",
        "phone",
        "user_type",
        "is_active",
        "is_verified",
        "connected_using",
        "last_logged_in",
    )
    list_filter = ("user_type", "is_active", "is_verified")
    search_fields = ("user_id", "name", "email", "phone")
    readonly_fields = ("user_id", "first_logged_in", "last_logged_in")
