import json
from decimal import Decimal, ROUND_HALF_UP

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models, transaction
from django.utils import timezone

DEPOSIT_RATE = Decimal("0.50")


def deposit_for(unit_price: Decimal, quantity: int) -> Decimal:
    total = unit_price * quantity
    return (total * DEPOSIT_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class Order(models.Model):
    """A buyer's reservation against a listing, paid by e-transfer deposit."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        READY_FOR_PICKUP = "ready_for_pickup", "Ready for pickup"
        COMPLETED = "completed", "Completed"
        EXPIRED = "expired", "Expired"

    buyer = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="orders",
    )
    listing = models.ForeignKey(
        "listings.Listing",
        on_delete=models.CASCADE,
        related_name="orders",
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=8, decimal_places=2)
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
        return f"Order {self.pk}"

    def refresh_status(self) -> "Order":
        if self.status in {self.Status.COMPLETED, self.Status.EXPIRED}:
            return self

        now = timezone.now()
        listing = self.listing
        if now > listing.pickup_end:
            with transaction.atomic():
                listing.quantity_available += self.quantity
                listing.sold_out = False
                listing.save(
                    update_fields=["quantity_available", "sold_out", "updated_at"]
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
            "dish_name": listing.dish_name,
            "photos": list(listing.photos or []),
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total": self.unit_price * self.quantity,
            "deposit_amount": self.deposit_amount,
            "deposit_rate": DEPOSIT_RATE,
            "deposit_sent": self.deposit_sent,
            "deposit_sent_at": self.deposit_sent_at,
            "status": self.status,
            "seller_name": seller.email or seller.user_id,
            "seller_etransfer_email": (
                profile.etransfer_email if profile is not None else ""
            ),
            "neighbourhood": listing.neighbourhood,
            "pickup_start": listing.pickup_start,
            "pickup_end": listing.pickup_end,
            "created_at": self.created_at,
        }
        return json.loads(json.dumps(raw, cls=DjangoJSONEncoder))
