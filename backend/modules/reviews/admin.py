from django.contrib import admin

from modules.admin_flow.site import StaffModelAdmin
from modules.reviews.models import Review


@admin.register(Review)
class ReviewAdmin(StaffModelAdmin, admin.ModelAdmin):
    list_display = ("seller", "buyer", "stars", "created_at")
    list_filter = ("stars",)
    search_fields = ("seller__name", "seller__email", "buyer__name", "comment")
