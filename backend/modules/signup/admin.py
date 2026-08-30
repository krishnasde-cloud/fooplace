from django.contrib import admin

from modules.admin_flow.site import StaffModelAdmin
from modules.signup.models import SellerProfile


@admin.register(SellerProfile)
class SellerProfileAdmin(StaffModelAdmin, admin.ModelAdmin):
    list_display = (
        "user",
        "neighbourhood",
        "has_food_handler_certification",
        "accepted_terms",
        "etransfer_email",
    )
    search_fields = ("user__email", "user__user_id", "user__name", "neighbourhood", "etransfer_email")
