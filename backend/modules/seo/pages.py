import json

from django.utils import timezone
from django.utils.safestring import mark_safe

from modules.backoffice.access import hidden_from_marketplace, listing_is_hidden
from modules.listings.models import Listing
from modules.listings.views import _listings_qs
from modules.reviews.profile import seller_public_api
from modules.users.models import User


def public_listings():
    return (
        _listings_qs()
        .filter(expires_at__gt=timezone.now())
        .exclude(hidden_from_marketplace())
        .order_by("-created_at")
    )


def browse_listings():
    return public_listings().filter(status=Listing.Status.ACTIVE)


def public_listing(listing_id: int) -> Listing | None:
    listing = _listings_qs().filter(pk=listing_id).first()
    if listing is None or listing_is_hidden(listing) or listing.is_expired:
        return None
    return listing


def public_sellers():
    return User.objects.filter(user_type=User.UserType.SELLER).order_by("pk")


def public_seller(seller_id: int) -> dict | None:
    result = seller_public_api(seller_id)
    if not isinstance(result, dict):
        return None
    return result


def absolute(request, path: str) -> str:
    return request.build_absolute_uri(path)


def browse_json_ld(request, listings) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Home-cooked near you",
        "url": absolute(request, "/"),
        "numberOfItems": len(listings),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": index,
                "url": absolute(request, f"/listings/{listing.pk}/"),
                "name": listing.dish_name,
            }
            for index, listing in enumerate(listings, start=1)
        ],
    }


def listing_json_ld(request, listing: Listing) -> dict:
    availability = (
        "https://schema.org/SoldOut" if listing.is_sold_out else "https://schema.org/InStock"
    )
    return {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": listing.dish_name,
        "description": listing.description,
        "url": absolute(request, f"/listings/{listing.pk}/"),
        "offers": {
            "@type": "Offer",
            "price": str(listing.price),
            "priceCurrency": "CAD",
            "availability": availability,
        },
    }


def seller_json_ld(request, profile: dict) -> dict:
    payload = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": profile["name"],
        "url": absolute(request, f"/sellers/{profile['id']}/"),
    }
    if profile.get("neighbourhood"):
        payload["homeLocation"] = profile["neighbourhood"]
    if profile.get("average_rating") is not None:
        payload["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": profile["average_rating"],
            "reviewCount": profile["review_count"],
        }
    return payload


def sitemap_urls(request) -> list[str]:
    urls = [absolute(request, "/")]
    urls.extend(absolute(request, f"/listings/{listing.pk}/") for listing in public_listings())
    urls.extend(absolute(request, f"/sellers/{seller.pk}/") for seller in public_sellers())
    return urls


def robots_text(request) -> str:
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "Allow: /listings\n"
        "Allow: /sellers\n"
        "Disallow: /sell\n"
        "Disallow: /orders\n"
        "Disallow: /admin\n"
        "Disallow: /api\n"
        f"Sitemap: {absolute(request, '/sitemap.xml')}\n"
    )


def json_ld_text(data: dict) -> str:
    return mark_safe(json.dumps(data, ensure_ascii=True).replace("<", "\\u003c"))
