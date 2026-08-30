import re
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import JsonResponse

from modules.listings.models import Listing

STREET_ADDRESS = re.compile(r"^\d+\s+\S+")
MAX_PHOTO_CHARS = 1_500_000
LISTING_FIELDS = (
    "photo",
    "dish_name",
    "description",
    "price",
    "quantity_available",
    "neighbourhood",
    "pickup_date",
    "pickup_window_start",
    "pickup_window_end",
    "status",
)


def listing_fields_from(
    data: dict, *, partial: bool = False
) -> tuple[dict | None, JsonResponse | None]:
    if not isinstance(data, dict):
        return None, JsonResponse({"detail": "invalid_json"}, status=400)

    fields: dict = {}
    required = LISTING_FIELDS if not partial else [key for key in LISTING_FIELDS if key in data]
    if partial and not required:
        return None, JsonResponse({"detail": "invalid_listing"}, status=400)

    parsers = {
        "photo": _photo,
        "dish_name": _dish_name,
        "description": _description,
        "price": _price,
        "quantity_available": _quantity,
        "neighbourhood": _neighbourhood,
        "pickup_date": _pickup_date,
        "pickup_window_start": _clock,
        "pickup_window_end": _clock,
        "status": _status,
    }
    for key in required:
        value, error = parsers[key](data.get(key))
        if error is not None:
            return None, error
        fields[key] = value

    if "quantity_available" in fields and fields["quantity_available"] == 0:
        fields["status"] = Listing.Status.SOLD_OUT
    elif not partial and "status" not in fields:
        fields["status"] = Listing.Status.ACTIVE

    start = fields.get("pickup_window_start")
    end = fields.get("pickup_window_end")
    if start is not None and end is not None and start >= end:
        return None, JsonResponse({"detail": "invalid_pickup"}, status=400)

    return fields, None


def _dish_name(value) -> tuple[str | None, JsonResponse | None]:
    name = str(value or "").strip()
    if not name or len(name) > 120:
        return None, JsonResponse({"detail": "invalid_listing"}, status=400)
    return name, None


def _description(value) -> tuple[str | None, JsonResponse | None]:
    text = str(value or "").strip()
    if not text:
        return None, JsonResponse({"detail": "invalid_listing"}, status=400)
    return text, None


def _price(value) -> tuple[Decimal | None, JsonResponse | None]:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError):
        return None, JsonResponse({"detail": "invalid_listing"}, status=400)
    if amount <= 0:
        return None, JsonResponse({"detail": "invalid_listing"}, status=400)
    return amount.quantize(Decimal("0.01")), None


def _quantity(value) -> tuple[int | None, JsonResponse | None]:
    try:
        count = int(value)
    except (TypeError, ValueError):
        return None, JsonResponse({"detail": "invalid_listing"}, status=400)
    if count < 0:
        return None, JsonResponse({"detail": "invalid_listing"}, status=400)
    return count, None


def _neighbourhood(value) -> tuple[str | None, JsonResponse | None]:
    name = str(value or "").strip()
    if not name or len(name) > 80:
        return None, JsonResponse({"detail": "invalid_listing"}, status=400)
    if STREET_ADDRESS.match(name):
        return None, JsonResponse({"detail": "exact_address_not_allowed"}, status=400)
    return name, None


def _pickup_date(value) -> tuple[date | None, JsonResponse | None]:
    raw = str(value or "").strip()
    try:
        return date.fromisoformat(raw), None
    except ValueError:
        return None, JsonResponse({"detail": "invalid_pickup"}, status=400)


def _clock(value) -> tuple[time | None, JsonResponse | None]:
    raw = str(value or "").strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(raw, fmt).time(), None
        except ValueError:
            continue
    return None, JsonResponse({"detail": "invalid_pickup"}, status=400)


def _status(value) -> tuple[str | None, JsonResponse | None]:
    if value not in {Listing.Status.ACTIVE, Listing.Status.SOLD_OUT}:
        return None, JsonResponse({"detail": "invalid_listing"}, status=400)
    return value, None


def _photo(value) -> tuple[str | None, JsonResponse | None]:
    photo = str(value or "").strip()
    if photo.startswith("data:image/") and len(photo) <= MAX_PHOTO_CHARS:
        return photo, None
    if photo.startswith(("http://", "https://")):
        try:
            URLValidator()(photo)
        except ValidationError:
            return None, JsonResponse({"detail": "invalid_photo"}, status=400)
        return photo, None
    return None, JsonResponse({"detail": "invalid_photo"}, status=400)
