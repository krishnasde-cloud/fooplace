from django.contrib import admin

from modules.admin_flow.site import StaffModelAdmin
from modules.orders.models import BuyerNotification, OrderHistory


@admin.register(OrderHistory)
class OrderHistoryAdmin(StaffModelAdmin, admin.ModelAdmin):
    list_display = ("order", "status", "note", "created_at")
    list_filter = ("status",)
    search_fields = ("order__listing__dish_name", "note")


@admin.register(BuyerNotification)
class BuyerNotificationAdmin(StaffModelAdmin, admin.ModelAdmin):
    list_display = ("buyer", "kind", "order", "created_at", "read_at")
    list_filter = ("kind",)
    search_fields = ("buyer__email", "message")
