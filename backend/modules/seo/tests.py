import json
import re
from datetime import date, time
from decimal import Decimal
from html.parser import HTMLParser

from django.test import TestCase
from django.utils import timezone

from modules.backoffice.models import ListingModeration
from modules.listings.models import Listing
from modules.seo.pages import browse_json_ld, listing_json_ld, robots_text, seller_json_ld, sitemap_urls
from modules.users.models import User

PHOTO = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQ"
    "AAAABJRU5ErkJggg=="
)


class _SeoDoc(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.robots = ""
        self.canonical = ""
        self.json_ld = None
        self._capture = ""
        self._in_title = False
        self._in_json = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self._in_title = True
            self._capture = ""
        if tag == "meta" and attrs.get("name") == "robots":
            self.robots = attrs.get("content", "")
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical = attrs.get("href", "")
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self._in_json = True
            self._capture = ""

    def handle_endtag(self, tag):
        if tag == "title" and self._in_title:
            self.title = self._capture
            self._in_title = False
        if tag == "script" and self._in_json:
            self.json_ld = json.loads(self._capture)
            self._in_json = False

    def handle_data(self, data):
        if self._in_title or self._in_json:
            self._capture += data


def _parse(html: str) -> _SeoDoc:
    doc = _SeoDoc()
    doc.feed(html)
    return doc


def _listing_fields(**overrides) -> dict:
    fields = {
        "photo": PHOTO,
        "dish_name": "Butter chicken",
        "description": "Homemade, mild spice, includes rice.",
        "price": Decimal("14.00"),
        "quantity_available": 4,
        "neighbourhood": "Kensington",
        "pickup_date": date(2026, 9, 2),
        "pickup_window_start": time(17, 0),
        "pickup_window_end": time(19, 0),
        "status": Listing.Status.ACTIVE,
    }
    fields.update(overrides)
    return fields


class SeoPageTests(TestCase):
    def setUp(self):
        now = timezone.now()
        self.seller = User.objects.create(
            user_id="user_seller",
            email="seller@example.com",
            user_type=User.UserType.SELLER,
            first_logged_in=now,
            last_logged_in=now,
        )
        self.buyer = User.objects.create(
            user_id="user_buyer",
            email="buyer@example.com",
            user_type=User.UserType.BUYER,
            first_logged_in=now,
            last_logged_in=now,
        )

    def _create_listing(self, **overrides) -> Listing:
        return Listing.objects.create(seller=self.seller, **_listing_fields(**overrides))

    def test_robots_txt_hides_signed_in_pages(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(
            {
                "status": response.status_code,
                "type": response["Content-Type"].split(";")[0],
                "body": response.content.decode(),
            },
            {
                "status": 200,
                "type": "text/plain",
                "body": robots_text(response.wsgi_request),
            },
        )
        self.assertEqual(
            robots_text(response.wsgi_request),
            "User-agent: *\n"
            "Allow: /\n"
            "Allow: /listings\n"
            "Allow: /sellers\n"
            "Disallow: /sell\n"
            "Disallow: /orders\n"
            "Disallow: /admin\n"
            "Disallow: /api\n"
            "Sitemap: http://testserver/sitemap.xml\n",
        )

    def test_sitemap_lists_public_listings_and_sellers_only(self):
        listing = self._create_listing()
        hidden = self._create_listing(dish_name="Hidden stew")
        ListingModeration.objects.create(listing=hidden, removed=True)
        response = self.client.get("/sitemap.xml")
        locs = re.findall(r"<loc>([^<]+)</loc>", response.content.decode())
        self.assertEqual(
            {
                "status": response.status_code,
                "type": response["Content-Type"].split(";")[0],
                "locs": locs,
            },
            {
                "status": 200,
                "type": "application/xml",
                "locs": sitemap_urls(response.wsgi_request),
            },
        )
        self.assertEqual(
            locs,
            [
                "http://testserver/",
                f"http://testserver/listings/{listing.pk}/",
                f"http://testserver/sellers/{self.seller.pk}/",
            ],
        )

    def test_browse_page_is_indexable_and_lists_dishes(self):
        listing = self._create_listing()
        response = self.client.get("/")
        doc = _parse(response.content.decode())
        self.assertEqual(
            {
                "status": response.status_code,
                "robots_header": response["X-Robots-Tag"],
                "title": doc.title,
                "robots": doc.robots,
                "canonical": doc.canonical,
                "json_ld": doc.json_ld,
            },
            {
                "status": 200,
                "robots_header": "index, follow",
                "title": "Home-cooked near you · Fooplace",
                "robots": "index, follow",
                "canonical": "http://testserver/",
                "json_ld": browse_json_ld(response.wsgi_request, [listing]),
            },
        )
        self.assertIn("Butter chicken", response.content.decode())
        self.assertIn(f"/listings/{listing.pk}/", response.content.decode())

    def test_listing_page_is_indexable(self):
        listing = self._create_listing()
        response = self.client.get(f"/listings/{listing.pk}/")
        doc = _parse(response.content.decode())
        self.assertEqual(
            {
                "status": response.status_code,
                "robots_header": response["X-Robots-Tag"],
                "title": doc.title,
                "robots": doc.robots,
                "canonical": doc.canonical,
                "json_ld": doc.json_ld,
            },
            {
                "status": 200,
                "robots_header": "index, follow",
                "title": "Butter chicken · Fooplace",
                "robots": "index, follow",
                "canonical": f"http://testserver/listings/{listing.pk}/",
                "json_ld": listing_json_ld(response.wsgi_request, listing),
            },
        )
        self.assertIn("Homemade, mild spice, includes rice.", response.content.decode())

    def test_seller_page_is_indexable(self):
        from modules.reviews.profile import seller_public_api

        response = self.client.get(f"/sellers/{self.seller.pk}/")
        doc = _parse(response.content.decode())
        profile = seller_public_api(self.seller.pk)
        self.assertEqual(
            {
                "status": response.status_code,
                "title": doc.title,
                "robots": doc.robots,
                "json_ld": doc.json_ld,
            },
            {
                "status": 200,
                "title": f"{self.seller.display_name} · Fooplace",
                "robots": "index, follow",
                "json_ld": seller_json_ld(response.wsgi_request, profile),
            },
        )

    def test_hidden_and_missing_listings_are_not_indexed(self):
        hidden = self._create_listing(dish_name="Hidden stew")
        ListingModeration.objects.create(listing=hidden, removed=True)
        self.assertEqual(
            {
                "hidden": self.client.get(f"/listings/{hidden.pk}/").status_code,
                "missing": self.client.get("/listings/999/").status_code,
                "buyer": self.client.get(f"/sellers/{self.buyer.pk}/").status_code,
            },
            {"hidden": 404, "missing": 404, "buyer": 404},
        )

    def test_signed_in_pages_are_not_server_rendered(self):
        self.assertEqual(
            {
                "sell": self.client.get("/sell/").status_code,
                "orders": self.client.get("/orders/").status_code,
                "order": self.client.get("/orders/1/").status_code,
            },
            {"sell": 404, "orders": 404, "order": 404},
        )
