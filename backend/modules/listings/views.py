from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from modules.listings.models import Listing


@require_GET
def index(request):
    neighbourhood = (request.GET.get("neighbourhood") or "").strip()
    cuisine = (request.GET.get("cuisine") or "").strip()
    query = (request.GET.get("q") or "").strip()

    listings = Listing.objects.select_related("seller").order_by("-created_at")
    if neighbourhood:
        listings = listings.filter(neighbourhood__iexact=neighbourhood)
    if cuisine:
        listings = listings.filter(cuisine__iexact=cuisine)
    if query:
        listings = listings.filter(
            Q(dish_name__icontains=query) | Q(description__icontains=query)
        )

    all_rows = Listing.objects.values_list("neighbourhood", "cuisine")
    neighbourhoods = sorted({row[0] for row in all_rows if row[0]})
    cuisines = sorted({row[1] for row in all_rows if row[1]})

    return JsonResponse(
        {
            "listings": [listing.as_api() for listing in listings],
            "filters": {"neighbourhoods": neighbourhoods, "cuisines": cuisines},
        }
    )


@require_GET
def detail(_request, listing_id):
    listing = Listing.objects.select_related("seller").filter(pk=listing_id).first()
    if listing is None:
        return JsonResponse({"detail": "not_found"}, status=404)
    return JsonResponse(listing.as_api())
