import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models


class Listing(models.Model):
    """A dish a seller is offering for neighbourhood pickup."""

    seller = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="listings",
    )
    dish_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    cuisine = models.CharField(max_length=64)
    neighbourhood = models.CharField(max_length=128)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity_available = models.PositiveIntegerField(default=1)
    photos = models.JSONField(default=list)
    pickup_start = models.DateTimeField()
    pickup_end = models.DateTimeField()
    sold_out = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.dish_name

    @property
    def is_sold_out(self) -> bool:
        return self.sold_out or self.quantity_available == 0

    def as_api(self) -> dict:
        seller = self.seller
        raw = {
            "id": self.pk,
            "dish_name": self.dish_name,
            "description": self.description,
            "cuisine": self.cuisine,
            "neighbourhood": self.neighbourhood,
            "price": self.price,
            "quantity_available": self.quantity_available,
            "photos": list(self.photos or []),
            "pickup_start": self.pickup_start,
            "pickup_end": self.pickup_end,
            "sold_out": self.is_sold_out,
            "seller_name": seller.email or seller.user_id,
        }
        return json.loads(json.dumps(raw, cls=DjangoJSONEncoder))
