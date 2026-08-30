from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone

from modules.listings.models import Listing, Order, deposit_for


def place_order(buyer, listing_id, quantity) -> Order | JsonResponse:
    if not isinstance(quantity, int) or quantity < 1:
        return JsonResponse({"detail": "invalid_quantity"}, status=400)

    now = timezone.now()
    with transaction.atomic():
        listing = (
            Listing.objects.select_for_update()
            .select_related("seller")
            .filter(pk=listing_id)
            .first()
        )
        if listing is None:
            return JsonResponse({"detail": "listing_not_found"}, status=404)
        if listing.is_sold_out or listing.pickup_end <= now:
            return JsonResponse({"detail": "listing_unavailable"}, status=400)
        if listing.seller_id == buyer.pk:
            return JsonResponse({"detail": "own_listing"}, status=400)
        if quantity > listing.quantity_available:
            return JsonResponse({"detail": "insufficient_quantity"}, status=400)

        listing.quantity_available -= quantity
        listing.status = (
            Listing.Status.SOLD_OUT
            if listing.quantity_available == 0
            else Listing.Status.ACTIVE
        )
        listing.save(update_fields=["quantity_available", "status", "updated_at"])
        return Order.objects.create(
            buyer=buyer,
            listing=listing,
            quantity=quantity,
            unit_price=listing.price,
            deposit_amount=deposit_for(listing.price, quantity),
            status=Order.Status.PENDING,
        )
