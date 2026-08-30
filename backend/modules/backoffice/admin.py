from django.contrib import admin

from modules.admin_flow.site import StaffModelAdmin
from modules.backoffice.models import ListingModeration, SellerReview


@admin.register(SellerReview)
class SellerReviewAdmin(StaffModelAdmin, admin.ModelAdmin):
    list_display = ("user", "status", "flagged", "removed", "note", "updated_at")
    list_filter = ("status", "flagged", "removed")
    search_fields = ("user__email", "user__user_id", "note")
    actions = ("approve_sellers", "reject_sellers", "flag_sellers", "remove_sellers")

    @admin.action(description="Approve selected sellers")
    def approve_sellers(self, request, queryset):
        queryset.update(status=SellerReview.Status.APPROVED, removed=False)

    @admin.action(description="Reject selected sellers")
    def reject_sellers(self, request, queryset):
        queryset.update(status=SellerReview.Status.REJECTED)

    @admin.action(description="Flag selected sellers")
    def flag_sellers(self, request, queryset):
        queryset.update(flagged=True)

    @admin.action(description="Remove selected sellers")
    def remove_sellers(self, request, queryset):
        queryset.update(removed=True, flagged=True)
        for review in queryset.select_related("user"):
            if review.user.is_active:
                review.user.is_active = False
                review.user.save(update_fields=["is_active"])


@admin.register(ListingModeration)
class ListingModerationAdmin(StaffModelAdmin, admin.ModelAdmin):
    list_display = ("listing", "flagged", "removed", "note", "updated_at")
    list_filter = ("flagged", "removed")
    search_fields = ("listing__dish_name", "listing__seller__email", "note")
    actions = ("flag_listings", "remove_listings", "restore_listings")

    @admin.action(description="Flag selected listings")
    def flag_listings(self, request, queryset):
        queryset.update(flagged=True)

    @admin.action(description="Remove selected listings")
    def remove_listings(self, request, queryset):
        queryset.update(removed=True, flagged=True)

    @admin.action(description="Restore selected listings")
    def restore_listings(self, request, queryset):
        queryset.update(removed=False, flagged=False)
