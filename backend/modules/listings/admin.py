from django.contrib import admin

from modules.admin_flow.site import StaffModelAdmin
from modules.listings.models import Listing, Order


@admin.register(Listing)
class ListingAdmin(StaffModelAdmin, admin.ModelAdmin):
    list_display = (
        "dish_name",
        "seller",
        "price",
        "quantity_available",
        "neighbourhood",
        "pickup_date",
        "status",
    )
    list_filter = ("status", "neighbourhood", "pickup_date")
    search_fields = ("dish_name", "neighbourhood", "seller__email")


@admin.register(Order)
class OrderAdmin(StaffModelAdmin, admin.ModelAdmin):
    list_display = ("listing", "buyer", "quantity", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("listing__dish_name", "buyer__email")
