import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models


class OrderHistory(models.Model):
    """Status change log for an order. Kept for later dispute handling."""

    order = models.ForeignKey(
        "listings.Order",
        on_delete=models.CASCADE,
        related_name="history",
    )
    status = models.CharField(max_length=16)
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def as_api(self) -> dict:
        raw = {
            "id": self.pk,
            "status": self.status,
            "note": self.note,
            "created_at": self.created_at,
        }
        return json.loads(json.dumps(raw, cls=DjangoJSONEncoder))


class BuyerNotification(models.Model):
    """In-app notice for a buyer when their order changes."""

    class Kind(models.TextChoices):
        EXPIRED = "expired", "Expired"
        CONFIRMED = "confirmed", "Confirmed"

    buyer = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="order_notifications",
    )
    order = models.ForeignKey(
        "listings.Order",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    kind = models.CharField(max_length=16, choices=Kind.choices)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def as_api(self) -> dict:
        raw = {
            "id": self.pk,
            "order_id": self.order_id,
            "kind": self.kind,
            "message": self.message,
            "created_at": self.created_at,
            "read_at": self.read_at,
            "dish_name": self.order.listing.dish_name,
        }
        return json.loads(json.dumps(raw, cls=DjangoJSONEncoder))
