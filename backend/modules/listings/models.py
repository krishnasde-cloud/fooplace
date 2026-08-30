import json

from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import MinValueValidator
from django.db import models


class Listing(models.Model):
    """A homemade dish a seller is offering for neighbourhood pickup."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SOLD_OUT = "sold_out", "Sold out"

    seller = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="listings",
    )
    photo = models.TextField()
    dish_name = models.CharField(max_length=120)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity_available = models.IntegerField(validators=[MinValueValidator(0)])
    neighbourhood = models.CharField(max_length=80)
    pickup_date = models.DateField()
    pickup_window_start = models.TimeField()
    pickup_window_end = models.TimeField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.dish_name

    def as_api(self) -> dict:
        raw = {
            "id": self.pk,
            "dish_name": self.dish_name,
            "description": self.description,
            "price": self.price,
            "quantity_available": self.quantity_available,
            "neighbourhood": self.neighbourhood,
            "pickup_date": self.pickup_date,
            "pickup_window_start": self.pickup_window_start,
            "pickup_window_end": self.pickup_window_end,
            "status": self.status,
            "photo": self.photo,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "order_status": self.order_status(),
        }
        return json.loads(json.dumps(raw, cls=DjangoJSONEncoder))

    def order_status(self) -> dict:
        counts = {status: 0 for status, _label in Order.Status.choices}
        for order in self.orders.all():
            counts[order.status] += 1
        return counts


class Order(models.Model):
    """A buyer reservation against a listing. Status is shown on the seller dashboard."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        PICKED_UP = "picked_up", "Picked up"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"

    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    buyer = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="orders",
    )
    quantity = models.PositiveIntegerField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.listing.dish_name} × {self.quantity}"

    def confirm_deadline(self):
        from datetime import timedelta

        from django.conf import settings

        hours = int(getattr(settings, "ORDER_CONFIRM_HOURS", 4))
        return self.created_at + timedelta(hours=hours)

    def as_api(self) -> dict:
        raw = {
            "id": self.pk,
            "listing_id": self.listing_id,
            "dish_name": self.listing.dish_name,
            "quantity": self.quantity,
            "status": self.status,
            "created_at": self.created_at,
            "confirm_by": self.confirm_deadline(),
            "buyer_email": self.buyer.email,
            "unit_price": self.listing.price,
            "history": [event.as_api() for event in self.history.all()],
        }
        return json.loads(json.dumps(raw, cls=DjangoJSONEncoder))
