from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, validate_email
from django.http import JsonResponse

from modules.geoapify.client import Geoapify, GeoapifyError
from modules.signup.models import SellerProfile
from modules.users.models import User


def apply_signup(user: User, data: dict) -> User | JsonResponse:
    user_type = data.get("type")
    if user_type not in {User.UserType.BUYER, User.UserType.SELLER}:
        return JsonResponse({"detail": "invalid_type"}, status=400)

    if user_type == User.UserType.BUYER:
        user.user_type = User.UserType.BUYER
        user.save(update_fields=["user_type"])
        SellerProfile.objects.filter(user=user).delete()
        return user

    seller_fields, error = seller_fields_from(data)
    if error is not None:
        return error

    user.user_type = User.UserType.SELLER
    user.save(update_fields=["user_type"])
    profile, _created = SellerProfile.objects.update_or_create(
        user=user,
        defaults=seller_fields,
    )
    user.seller_profile = profile
    return user


def clean_text(value: object) -> str:
    return "".join(char for char in str(value or "").strip() if char.isprintable())


def marketplace_url(value: str) -> str:
    if value and "://" not in value:
        return f"https://{value}"
    return value


def seller_fields_from(data: dict) -> tuple[dict | None, JsonResponse | None]:
    if data.get("accepted_terms") is not True:
        return None, JsonResponse({"detail": "terms_required"}, status=400)

    url = marketplace_url(clean_text(data.get("facebook_marketplace_url")))
    email = clean_text(data.get("etransfer_email"))
    address = clean_text(data.get("pickup_address"))
    try:
        URLValidator()(url)
        validate_email(email)
    except ValidationError:
        return None, JsonResponse({"detail": "invalid_seller_details"}, status=400)
    if not address:
        return None, JsonResponse({"detail": "invalid_seller_details"}, status=400)

    try:
        place = Geoapify().geocode(address)
    except GeoapifyError:
        return None, JsonResponse({"detail": "geocode_unavailable"}, status=503)
    if place is None:
        return None, JsonResponse({"detail": "invalid_pickup_address"}, status=400)

    return (
        {
            "has_food_handler_certification": bool(
                data.get("has_food_handler_certification")
            ),
            "accepted_terms": True,
            "facebook_marketplace_url": url,
            "etransfer_email": email,
            "pickup_address": place.formatted,
            "pickup_lat": place.lat,
            "pickup_lon": place.lon,
        },
        None,
    )
