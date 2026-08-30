from django.contrib import admin

from modules.admin_flow.site import StaffModelAdmin
from modules.backoffice.actions import apply_listing_moderation
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
        "flagged",
        "removed",
    )
    list_filter = (
        "status",
        "neighbourhood",
        "cuisine",
        "pickup_date",
        "moderation__flagged",
        "moderation__removed",
    )
    search_fields = ("dish_name", "neighbourhood", "seller__email")
    actions = ("flag_listings", "unflag_listings", "remove_listings", "restore_listings")
    list_select_related = ("seller", "moderation")

    @admin.display(boolean=True, description="Flagged")
    def flagged(self, listing):
        moderation = getattr(listing, "moderation", None)
        return bool(moderation is not None and moderation.flagged)

    @admin.display(boolean=True, description="Removed")
    def removed(self, listing):
        moderation = getattr(listing, "moderation", None)
        return bool(moderation is not None and moderation.removed)

    @admin.action(description="Flag selected listings")
    def flag_listings(self, request, queryset):
        for listing in queryset:
            apply_listing_moderation(listing, "flag")

    @admin.action(description="Clear flag on selected listings")
    def unflag_listings(self, request, queryset):
        for listing in queryset:
            apply_listing_moderation(listing, "unflag")

    @admin.action(description="Remove selected listings")
    def remove_listings(self, request, queryset):
        for listing in queryset:
            apply_listing_moderation(listing, "remove")

    @admin.action(description="Restore selected listings")
    def restore_listings(self, request, queryset):
        for listing in queryset:
            apply_listing_moderation(listing, "restore")


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
