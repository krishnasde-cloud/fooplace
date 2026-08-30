import json
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone

DEPOSIT_RATE = Decimal("0.50")
LISTING_LIFETIME = timedelta(hours=24)


def default_expires_at():
    return timezone.now() + LISTING_LIFETIME


def deposit_for(unit_price: Decimal, quantity: int) -> Decimal:
    total = unit_price * quantity
    return (total * DEPOSIT_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _aware(value: datetime) -> datetime:
    if timezone.is_naive(value):
        return timezone.make_aware(value)
    return value


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
    cuisine = models.CharField(max_length=64, blank=True)
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
    expires_at = models.DateTimeField(default=default_expires_at)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.dish_name

    @property
    def is_sold_out(self) -> bool:
        return self.status == self.Status.SOLD_OUT or self.quantity_available == 0

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    def relist(self) -> "Listing":
        self.expires_at = default_expires_at()
        if self.quantity_available > 0:
            self.status = self.Status.ACTIVE
        self.save(update_fields=["expires_at", "status", "updated_at"])
        return self

    @property
    def pickup_start(self) -> datetime:
        return _aware(datetime.combine(self.pickup_date, self.pickup_window_start))

    @property
    def pickup_end(self) -> datetime:
        return _aware(datetime.combine(self.pickup_date, self.pickup_window_end))

    def as_api(self) -> dict:
        seller = self.seller
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
            "expires_at": self.expires_at,
            "expired": self.is_expired,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "order_status": self.order_status(),
            "cuisine": self.cuisine,
            "photos": [self.photo] if self.photo else [],
            "sold_out": self.is_sold_out,
            "seller_name": seller.email or seller.user_id,
            "pickup_start": self.pickup_start,
            "pickup_end": self.pickup_end,
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
        READY_FOR_PICKUP = "ready_for_pickup", "Ready for pickup"
        COMPLETED = "completed", "Completed"
        EXPIRED = "expired", "Expired"
        PICKED_UP = "picked_up", "Picked up"
        CANCELLED = "cancelled", "Cancelled"

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
    unit_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    deposit_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    deposit_sent = models.BooleanField(default=False)
    deposit_sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.listing.dish_name} × {self.quantity}"

    def refresh_status(self) -> "Order":
        if self.status in {
            self.Status.COMPLETED,
            self.Status.EXPIRED,
            self.Status.PICKED_UP,
            self.Status.CANCELLED,
        }:
            return self

        now = timezone.now()
        listing = self.listing
        if now > listing.pickup_end:
            with transaction.atomic():
                listing.quantity_available += self.quantity
                listing.status = (
                    Listing.Status.SOLD_OUT
                    if listing.quantity_available == 0
                    else Listing.Status.ACTIVE
                )
                listing.save(
                    update_fields=["quantity_available", "status", "updated_at"]
                )
                self.status = self.Status.EXPIRED
                self.save(update_fields=["status", "updated_at"])
            return self

        if self.deposit_sent and now >= listing.pickup_start:
            self.status = self.Status.READY_FOR_PICKUP
            self.save(update_fields=["status", "updated_at"])
        return self

    def as_api(self) -> dict:
        listing = self.listing
        seller = listing.seller
        profile = getattr(seller, "seller_profile", None)
        raw = {
            "id": self.pk,
            "listing_id": listing.pk,
            "quantity": self.quantity,
            "status": self.status,
            "created_at": self.created_at,
            "dish_name": listing.dish_name,
            "photos": [listing.photo] if listing.photo else [],
            "unit_price": self.unit_price,
            "total": self.unit_price * self.quantity,
            "deposit_amount": self.deposit_amount,
            "deposit_rate": DEPOSIT_RATE,
            "deposit_sent": self.deposit_sent,
            "deposit_sent_at": self.deposit_sent_at,
            "seller_name": seller.email or seller.user_id,
            "seller_etransfer_email": (
                profile.etransfer_email if profile is not None else ""
            ),
            "neighbourhood": listing.neighbourhood,
            "pickup_start": listing.pickup_start,
            "pickup_end": listing.pickup_end,
        }
        return json.loads(json.dumps(raw, cls=DjangoJSONEncoder))
