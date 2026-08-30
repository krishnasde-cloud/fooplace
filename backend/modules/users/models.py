import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models


class User(models.Model):
    """App user linked to a Clerk account by `user_id`."""

    class UserType(models.TextChoices):
        BUYER = "buyer", "Buyer"
        SELLER = "seller", "Seller"
        ADMIN = "admin", "Admin"

    user_id = models.CharField(max_length=64, unique=True)
    email = models.EmailField(blank=True)
    connected_using = models.CharField(max_length=64, blank=True)
    user_type = models.CharField(
        max_length=16,
        choices=UserType.choices,
        blank=True,
        default="",
    )
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    first_logged_in = models.DateTimeField()
    last_logged_in = models.DateTimeField()

    def __str__(self) -> str:
        return self.email or self.user_id

    @property
    def is_admin(self) -> bool:
        return self.user_type == self.UserType.ADMIN

    def as_api(self) -> dict:
        raw = {
            "user_id": self.user_id,
            "email": self.email,
            "connected_using": self.connected_using,
            "type": self.user_type,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "first_logged_in": self.first_logged_in,
            "last_logged_in": self.last_logged_in,
            "seller": self._seller_api(),
            "review": self._review_api(),
        }
        return json.loads(json.dumps(raw, cls=DjangoJSONEncoder))

    def _seller_api(self) -> dict | None:
        seller = getattr(self, "seller_profile", None)
        if seller is None:
            return None
        return seller.as_api()

    def _review_api(self) -> dict | None:
        review = getattr(self, "seller_review", None)
        if review is None:
            return None
        return review.as_api()
