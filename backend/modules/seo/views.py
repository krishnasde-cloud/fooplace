import json
import os

from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_GET

from modules.seo.pages import (
    browse_json_ld,
    browse_listings,
    json_ld_text,
    listing_json_ld,
    public_listing,
    public_seller,
    robots_text,
    seller_json_ld,
    sitemap_urls,
)


def _spa_assets() -> dict:
    if settings.DEBUG and not os.environ.get("VERCEL"):
        return {"js": "", "css": ""}
    return {"js": "/assets/index.js", "css": "/assets/index.css"}


def _page(request, *, title, description, canonical, json_ld, ssr_data, template, extra):
    context = {
        "title": title,
        "description": description,
        "canonical": canonical,
        "robots": "index, follow",
        "json_ld": json_ld_text(json_ld),
        "ssr_data": mark_safe(json.dumps(ssr_data).replace("<", "\\u003c")),
        "spa": _spa_assets(),
        **extra,
    }
    response = render(request, template, context)
    response["X-Robots-Tag"] = "index, follow"
    return response


@require_GET
def robots(request):
    return HttpResponse(robots_text(request), content_type="text/plain")


@require_GET
def sitemap(request):
    locs = "".join(f"  <url><loc>{url}</loc></url>\n" for url in sitemap_urls(request))
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{locs}"
        "</urlset>\n"
    )
    return HttpResponse(body, content_type="application/xml")


@require_GET
def browse(request):
    listings = list(browse_listings())
    return _page(
        request,
        title="Home-cooked near you · Fooplace",
        description="Browse homemade dishes for neighbourhood pickup on Fooplace.",
        canonical=request.build_absolute_uri("/"),
        json_ld=browse_json_ld(request, listings),
        ssr_data={"listings": [item.as_api() for item in listings]},
        template="seo/browse.html",
        extra={"listings": listings},
    )


@require_GET
def listing(request, listing_id: int):
    item = public_listing(listing_id)
    if item is None:
        raise Http404("not_found")
    return _page(
        request,
        title=f"{item.dish_name} · Fooplace",
        description=item.description,
        canonical=request.build_absolute_uri(f"/listings/{item.pk}/"),
        json_ld=listing_json_ld(request, item),
        ssr_data={"listing": item.as_api()},
        template="seo/listing.html",
        extra={"listing": item},
    )


@require_GET
def seller(request, seller_id: int):
    profile = public_seller(seller_id)
    if profile is None:
        raise Http404("not_found")
    return _page(
        request,
        title=f"{profile['name']} · Fooplace",
        description=f"Public seller profile for {profile['name']} on Fooplace.",
        canonical=request.build_absolute_uri(f"/sellers/{profile['id']}/"),
        json_ld=seller_json_ld(request, profile),
        ssr_data={"seller": profile},
        template="seo/seller.html",
        extra={"seller": profile},
    )
