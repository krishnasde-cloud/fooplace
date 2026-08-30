from django.contrib import admin

from modules.admin_flow.site import StaffModelAdmin
from modules.backoffice.actions import apply_seller_review
from modules.backoffice.models import ListingModeration, SellerReview


@admin.register(SellerReview)
class SellerReviewAdmin(StaffModelAdmin, admin.ModelAdmin):
    list_display = ("user", "status", "flagged", "removed", "note", "updated_at")
    list_filter = ("status", "flagged", "removed")
    search_fields = ("user__email", "user__user_id", "note")
    actions = (
        "approve_sellers",
        "reject_sellers",
        "flag_sellers",
        "unflag_sellers",
        "remove_sellers",
        "restore_sellers",
    )

    @admin.action(description="Approve selected sellers")
    def approve_sellers(self, request, queryset):
        for review in queryset.select_related("user"):
            apply_seller_review(review, "approve")

    @admin.action(description="Reject selected sellers")
    def reject_sellers(self, request, queryset):
        for review in queryset.select_related("user"):
            apply_seller_review(review, "reject")

    @admin.action(description="Flag selected sellers")
    def flag_sellers(self, request, queryset):
        for review in queryset.select_related("user"):
            apply_seller_review(review, "flag")

    @admin.action(description="Clear flag on selected sellers")
    def unflag_sellers(self, request, queryset):
        for review in queryset.select_related("user"):
            apply_seller_review(review, "unflag")

    @admin.action(description="Remove selected sellers")
    def remove_sellers(self, request, queryset):
        for review in queryset.select_related("user"):
            apply_seller_review(review, "remove")

    @admin.action(description="Restore selected sellers")
    def restore_sellers(self, request, queryset):
        for review in queryset.select_related("user"):
            apply_seller_review(review, "restore")


@admin.register(ListingModeration)
class ListingModerationAdmin(StaffModelAdmin, admin.ModelAdmin):
    list_display = ("listing", "flagged", "removed", "note", "updated_at")
    list_filter = ("flagged", "removed")
    search_fields = ("listing__dish_name", "listing__seller__email", "note")
