from datetime import time, timedelta

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
        "photo": "https://images.unsplash.com/photo-1559314809-0d155014e29e?auto=format&fit=crop&w=800&q=80",
        "pickup_offset_days": 0,
        "pickup_window_start": time(17, 0),
        "pickup_window_end": time(21, 0),
    },
    {
        "dish_name": "Birria tacos",
        "description": "Three tacos with consomé for dipping.",
        "cuisine": "Mexican",
        "neighbourhood": "Leslieville",
        "price": "18.00",
        "quantity_available": 6,
        "photo": "https://images.unsplash.com/photo-1551504734-5ee1c4a1479b?auto=format&fit=crop&w=800&q=80",
        "pickup_offset_days": 0,
        "pickup_window_start": time(12, 0),
        "pickup_window_end": time(20, 0),
    },
    {
        "dish_name": "Lasagna al forno",
        "description": "Beef ragu, béchamel, and a side salad.",
        "cuisine": "Italian",
        "neighbourhood": "Kensington",
        "price": "22.00",
        "quantity_available": 4,
        "photo": "https://images.unsplash.com/photo-1574894709920-11b28e7367e3?auto=format&fit=crop&w=800&q=80",
        "pickup_offset_days": 1,
        "pickup_window_start": time(16, 0),
        "pickup_window_end": time(20, 0),
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

        today = timezone.localdate()
        for item in SEED_LISTINGS:
            Listing.objects.create(
                seller=seller,
                dish_name=item["dish_name"],
                description=item["description"],
                cuisine=item["cuisine"],
                neighbourhood=item["neighbourhood"],
                price=item["price"],
                quantity_available=item["quantity_available"],
                photo=item["photo"],
                pickup_date=today + timedelta(days=item["pickup_offset_days"]),
                pickup_window_start=item["pickup_window_start"],
                pickup_window_end=item["pickup_window_end"],
                status=Listing.Status.ACTIVE,
            )

        self.stdout.write(f"Seeded {len(SEED_LISTINGS)} listings.")
