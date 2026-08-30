from django.db import models


class SellerReview(models.Model):
    """Admin decision on a seller account: approve, reject, flag, or remove."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.OneToOneField(
        "users.User",
        on_delete=models.CASCADE,
        related_name="seller_review",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    flagged = models.BooleanField(default=False)
    removed = models.BooleanField(default=False)
    note = models.CharField(max_length=240, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user} ({self.status})"

    def can_sell(self) -> bool:
        return self.status == self.Status.APPROVED and not self.removed

    def as_api(self) -> dict:
        return {
            "status": self.status,
            "flagged": self.flagged,
            "removed": self.removed,
            "note": self.note,
        }


class ListingModeration(models.Model):
    """Admin kill switch for a listing, without deleting the row."""

    listing = models.OneToOneField(
        "listings.Listing",
        on_delete=models.CASCADE,
        related_name="moderation",
    )
    flagged = models.BooleanField(default=False)
    removed = models.BooleanField(default=False)
    note = models.CharField(max_length=240, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.listing} moderation"

    def as_api(self) -> dict:
        return {
            "flagged": self.flagged,
            "removed": self.removed,
            "note": self.note,
        }
