import json

from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
    """A buyer's 1-5 star rating of a seller after a completed order."""

    order = models.OneToOneField(
        "listings.Order",
        on_delete=models.CASCADE,
        related_name="review",
    )
    buyer = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="reviews_left",
    )
    seller = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="reviews_received",
    )
    stars = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.stars}★ for {self.seller_id}"

    def as_api(self) -> dict:
        raw = {
            "id": self.pk,
            "stars": self.stars,
            "comment": self.comment,
            "created_at": self.created_at,
            "buyer_name": self.buyer.display_name,
        }
        return json.loads(json.dumps(raw, cls=DjangoJSONEncoder))
