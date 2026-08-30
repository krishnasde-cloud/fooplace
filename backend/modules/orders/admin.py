from django.contrib import admin

from modules.admin_flow.site import StaffModelAdmin
from modules.orders.models import Order


@admin.register(Order)
class OrderAdmin(StaffModelAdmin, admin.ModelAdmin):
    list_display = (
        "id",
        "buyer",
        "listing",
        "quantity",
        "deposit_amount",
        "deposit_sent",
        "status",
        "created_at",
    )
    list_filter = ("status", "deposit_sent")
    search_fields = ("buyer__email", "listing__dish_name")
