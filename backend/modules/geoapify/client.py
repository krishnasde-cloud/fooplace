"""Server-side Geoapify client. The API key never leaves Django."""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from django.conf import settings

GEOCODE_URL = "https://api.geoapify.com/v1/geocode"


@dataclass(frozen=True)
class Place:
    formatted: str
    lat: float
    lon: float

    def as_api(self) -> dict:
        return {"formatted": self.formatted, "lat": self.lat, "lon": self.lon}


class GeoapifyError(Exception):
    """Geoapify could not complete a request."""


class Geoapify:
    """Lookup and autocomplete addresses with GEOAPIFY_API_KEY."""

    def __init__(self, api_key: str | None = None):
        self.api_key = settings.GEOAPIFY_API_KEY if api_key is None else api_key

    def autocomplete(self, text: str, *, limit: int = 5) -> list[Place]:
        text = text.strip()
        if not text:
            return []
        return self._places("autocomplete", text, limit)

    def geocode(self, text: str) -> Place | None:
        text = text.strip()
        if not text:
            return None
        places = self._places("search", text, 1)
        return places[0] if places else None

    def _places(self, path: str, text: str, limit: int) -> list[Place]:
        if not self.api_key:
            raise GeoapifyError("missing_api_key")
        query = urlencode(
            {
                "text": text,
                "limit": limit,
                "format": "json",
                "apiKey": self.api_key,
            }
        )
        try:
            with urlopen(f"{GEOCODE_URL}/{path}?{query}", timeout=8) as response:
                payload = json.loads(response.read().decode())
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
            raise GeoapifyError("request_failed") from exc
        if not isinstance(payload, dict):
            raise GeoapifyError("request_failed")
        places = []
        for item in payload.get("results") or []:
            place = _place(item)
            if place is not None:
                places.append(place)
        return places


def _place(item: object) -> Place | None:
    if not isinstance(item, dict):
        return None
    formatted = str(item.get("formatted") or "").strip()
    try:
        lat = float(item["lat"])
        lon = float(item["lon"])
    except (KeyError, TypeError, ValueError):
        return None
    if not formatted:
        return None
    return Place(formatted=formatted, lat=lat, lon=lon)
