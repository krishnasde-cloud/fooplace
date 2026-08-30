from django.db import models


class SellerProfile(models.Model):
    """Seller details collected during signup."""

    user = models.OneToOneField(
        "users.User",
        on_delete=models.CASCADE,
        related_name="seller_profile",
    )
    has_food_handler_certification = models.BooleanField(default=False)
    accepted_terms = models.BooleanField(default=False)
    facebook_marketplace_url = models.URLField(max_length=500, blank=True)
    etransfer_email = models.EmailField(blank=True)

    def as_api(self) -> dict:
        return {
            "has_food_handler_certification": self.has_food_handler_certification,
            "accepted_terms": self.accepted_terms,
            "facebook_marketplace_url": self.facebook_marketplace_url,
            "etransfer_email": self.etransfer_email,
        }
