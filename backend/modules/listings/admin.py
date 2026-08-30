from django.contrib import admin

from modules.admin_flow.site import StaffModelAdmin
from modules.listings.models import Listing, Order


@admin.register(Listing)
class ListingAdmin(StaffModelAdmin, admin.ModelAdmin):
    list_display = (
        "dish_name",
        "seller",
        "cuisine",
        "price",
        "quantity_available",
        "neighbourhood",
        "pickup_date",
        "status",
    )
    list_filter = ("status", "neighbourhood", "cuisine", "pickup_date")
    search_fields = ("dish_name", "neighbourhood", "seller__email")


@admin.register(Order)
class OrderAdmin(StaffModelAdmin, admin.ModelAdmin):
    list_display = (
        "listing",
        "buyer",
        "quantity",
        "deposit_amount",
        "deposit_sent",
        "status",
        "created_at",
    )
    list_filter = ("status", "deposit_sent")
    search_fields = ("listing__dish_name", "buyer__email")
