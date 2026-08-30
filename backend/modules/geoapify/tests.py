import json
from io import BytesIO
from unittest.mock import patch
from urllib.error import URLError

from django.test import TestCase, override_settings

from modules.geoapify.client import Geoapify, GeoapifyError, Place


def _http(payload: dict):
    return BytesIO(json.dumps(payload).encode())


QUEEN = Place(
    formatted="123 Queen St W, Toronto, ON, Canada",
    lat=43.652,
    lon=-79.38,
)


class GeoapifyTests(TestCase):
    @override_settings(GEOAPIFY_API_KEY="test-key")
    @patch("modules.geoapify.client.urlopen")
    def test_autocomplete_maps_results(self, mock_urlopen):
        mock_urlopen.return_value = _http(
            {
                "results": [
                    {
                        "formatted": QUEEN.formatted,
                        "lat": QUEEN.lat,
                        "lon": QUEEN.lon,
                    }
                ]
            }
        )
        self.assertEqual(Geoapify().autocomplete("123 Queen"), [QUEEN])

    @override_settings(GEOAPIFY_API_KEY="test-key")
    @patch("modules.geoapify.client.urlopen")
    def test_geocode_returns_first_place(self, mock_urlopen):
        mock_urlopen.return_value = _http(
            {
                "results": [
                    {
                        "formatted": QUEEN.formatted,
                        "lat": QUEEN.lat,
                        "lon": QUEEN.lon,
                    }
                ]
            }
        )
        self.assertEqual(Geoapify().geocode("123 Queen St W, Toronto"), QUEEN)

    @override_settings(GEOAPIFY_API_KEY="test-key")
    @patch("modules.geoapify.client.urlopen")
    def test_geocode_empty_results(self, mock_urlopen):
        mock_urlopen.return_value = _http({"results": []})
        self.assertEqual(Geoapify().geocode("nowhere"), None)

    @override_settings(GEOAPIFY_API_KEY="")
    def test_missing_key_raises(self):
        with self.assertRaises(GeoapifyError):
            Geoapify().geocode("123 Queen")

    @override_settings(GEOAPIFY_API_KEY="test-key")
    @patch("modules.geoapify.client.urlopen", side_effect=URLError("down"))
    def test_network_error_raises(self, _mock_urlopen):
        with self.assertRaises(GeoapifyError):
            Geoapify().autocomplete("123 Queen")


class AutocompleteViewTests(TestCase):
    def test_short_text_is_empty(self):
        response = self.client.get("/api/geoapify/autocomplete/", {"text": "ab"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"results": []})

    @override_settings(GEOAPIFY_API_KEY="test-key")
    @patch("modules.geoapify.views.Geoapify.autocomplete", return_value=[QUEEN])
    def test_autocomplete_is_public(self, _mock_autocomplete):
        response = self.client.get("/api/geoapify/autocomplete/", {"text": "123 Queen"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"results": [QUEEN.as_api()]})

    @override_settings(GEOAPIFY_API_KEY="")
    def test_missing_key_is_unavailable(self):
        response = self.client.get("/api/geoapify/autocomplete/", {"text": "123 Queen"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"detail": "geocode_unavailable"})
