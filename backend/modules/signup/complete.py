from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, validate_email
from django.http import JsonResponse

from modules.geoapify.client import Geoapify, GeoapifyError
from modules.listings.payload import STREET_ADDRESS
from modules.signup.models import SellerProfile
from modules.users.models import User


def apply_signup(user: User, data: dict) -> User | JsonResponse:
    user_type = data.get("type")
    if user_type not in {User.UserType.BUYER, User.UserType.SELLER}:
        return JsonResponse({"detail": "invalid_type"}, status=400)

    account, error = account_fields_from(data, user)
    if error is not None:
        return error

    user.name = account["name"]
    user.phone = account["phone"]
    user.user_type = user_type

    if user_type == User.UserType.BUYER:
        user.save(update_fields=["user_type", "name", "phone"])
        SellerProfile.objects.filter(user=user).delete()
        return user

    seller_fields, error = seller_fields_from(data)
    if error is not None:
        return error

    user.save(update_fields=["user_type", "name", "phone"])
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


def account_fields_from(data: dict, user: User) -> tuple[dict | None, JsonResponse | None]:
    name = clean_text(data.get("name"))
    phone = clean_text(data.get("phone"))
    if not name or len(name) > 80:
        return None, JsonResponse({"detail": "name_required"}, status=400)
    if phone and len(phone) > 32:
        return None, JsonResponse({"detail": "invalid_phone"}, status=400)
    if not phone and not user.email:
        return None, JsonResponse({"detail": "contact_required"}, status=400)
    return {"name": name, "phone": phone}, None


def neighbourhood_from(data: dict) -> tuple[str | None, JsonResponse | None]:
    name = clean_text(data.get("neighbourhood"))
    if not name or len(name) > 80:
        return None, JsonResponse({"detail": "invalid_neighbourhood"}, status=400)
    if STREET_ADDRESS.match(name):
        return None, JsonResponse({"detail": "exact_address_not_allowed"}, status=400)
    return name, None


def seller_fields_from(data: dict) -> tuple[dict | None, JsonResponse | None]:
    if data.get("accepted_terms") is not True:
        return None, JsonResponse({"detail": "terms_required"}, status=400)

    neighbourhood, error = neighbourhood_from(data)
    if error is not None:
        return None, error

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
            "neighbourhood": neighbourhood,
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
