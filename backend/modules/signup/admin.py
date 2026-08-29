from django.contrib import admin

from modules.signup.models import SellerProfile


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "has_food_handler_certification",
        "accepted_terms",
        "etransfer_email",
    )
    search_fields = ("user__email", "user__user_id", "etransfer_email")
