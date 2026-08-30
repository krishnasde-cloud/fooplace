from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from modules.listings.models import Listing
from modules.signup.models import SellerProfile
from modules.users.models import User

SEED_LISTINGS = (
    {
        "dish_name": "Pad Thai",
        "description": "Tamarind noodles with tofu, peanuts, and lime.",
        "cuisine": "Thai",
        "neighbourhood": "Kensington",
        "price": "16.00",
        "quantity_available": 8,
        "photos": [
            "https://images.unsplash.com/photo-1559314809-0d155014e29e?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=800&q=80",
        ],
        "start_offset": timedelta(hours=2),
        "end_offset": timedelta(hours=8),
    },
    {
        "dish_name": "Birria tacos",
        "description": "Three tacos with consomé for dipping.",
        "cuisine": "Mexican",
        "neighbourhood": "Leslieville",
        "price": "18.00",
        "quantity_available": 6,
        "photos": [
            "https://images.unsplash.com/photo-1551504734-5ee1c4a1479b?auto=format&fit=crop&w=800&q=80",
        ],
        "start_offset": timedelta(hours=-1),
        "end_offset": timedelta(hours=5),
    },
    {
        "dish_name": "Lasagna al forno",
        "description": "Beef ragu, béchamel, and a side salad.",
        "cuisine": "Italian",
        "neighbourhood": "Kensington",
        "price": "22.00",
        "quantity_available": 4,
        "photos": [
            "https://images.unsplash.com/photo-1574894709920-11b28e7367e3?auto=format&fit=crop&w=800&q=80",
        ],
        "start_offset": timedelta(days=1),
        "end_offset": timedelta(days=1, hours=4),
    },
)


class Command(BaseCommand):
    help = "Create demo seller listings when the table is empty."

    def handle(self, *args, **options):
        if Listing.objects.exists():
            self.stdout.write("Listings already exist; skipping seed.")
            return

        now = timezone.now()
        seller, _created = User.objects.get_or_create(
            user_id="seed_seller",
            defaults={
                "email": "kitchen@fooplace.local",
                "user_type": User.UserType.SELLER,
                "is_active": True,
                "is_verified": True,
                "first_logged_in": now,
                "last_logged_in": now,
            },
        )
        SellerProfile.objects.get_or_create(
            user=seller,
            defaults={
                "has_food_handler_certification": True,
                "accepted_terms": True,
                "facebook_marketplace_url": "https://www.facebook.com/marketplace/profile/fooplace",
                "etransfer_email": "payouts@fooplace.local",
            },
        )

        for item in SEED_LISTINGS:
            Listing.objects.create(
                seller=seller,
                dish_name=item["dish_name"],
                description=item["description"],
                cuisine=item["cuisine"],
                neighbourhood=item["neighbourhood"],
                price=item["price"],
                quantity_available=item["quantity_available"],
                photos=item["photos"],
                pickup_start=now + item["start_offset"],
                pickup_end=now + item["end_offset"],
            )

        self.stdout.write(f"Seeded {len(SEED_LISTINGS)} listings.")
