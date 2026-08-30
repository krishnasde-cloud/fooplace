from django.contrib import admin

from modules.admin_flow.site import StaffModelAdmin
from modules.listings.models import Listing


@admin.register(Listing)
class ListingAdmin(StaffModelAdmin, admin.ModelAdmin):
    list_display = (
        "dish_name",
        "seller",
        "cuisine",
        "neighbourhood",
        "price",
        "quantity_available",
        "sold_out",
        "pickup_start",
    )
    list_filter = ("cuisine", "neighbourhood", "sold_out")
    search_fields = ("dish_name", "description", "seller__email")
