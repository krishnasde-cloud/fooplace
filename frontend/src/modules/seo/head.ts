import type { Listing } from "@/modules/listings/types.ts";
import type { SellerProfile } from "@/modules/reviews/types.ts";
import { listingIdFromPath, sellerIdFromPath } from "./publicPath.ts";

export type Robots = "index, follow" | "noindex, nofollow";

export type SeoDocument = {
  title: string;
  description: string;
  robots: Robots;
  canonical: string;
  jsonLd: Record<string, unknown> | null;
};

function originJoin(origin: string, path: string): string {
  return `${origin.replace(/\/$/, "")}${path}`;
}

export function browseJsonLd(origin: string, listings: Listing[]): Record<string, unknown> {
  return {
    "@context": "https://schema.org",
    "@type": "ItemList",
    name: "Home-cooked near you",
    url: originJoin(origin, "/"),
    numberOfItems: listings.length,
    itemListElement: listings.map((listing, index) => ({
      "@type": "ListItem",
      position: index + 1,
      url: originJoin(origin, `/listings/${listing.id}/`),
      name: listing.dish_name,
    })),
  };
}

export function listingJsonLd(origin: string, listing: Listing): Record<string, unknown> {
  return {
    "@context": "https://schema.org",
    "@type": "Product",
    name: listing.dish_name,
    description: listing.description,
    url: originJoin(origin, `/listings/${listing.id}/`),
    offers: {
      "@type": "Offer",
      price: String(listing.price),
      priceCurrency: "CAD",
      availability: listing.sold_out
        ? "https://schema.org/SoldOut"
        : "https://schema.org/InStock",
    },
  };
}

export function sellerJsonLd(origin: string, profile: SellerProfile): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@type": "Person",
    name: profile.name,
    url: originJoin(origin, `/sellers/${profile.id}/`),
  };
  if (profile.neighbourhood) {
    payload.homeLocation = profile.neighbourhood;
  }
  if (profile.average_rating != null) {
    payload.aggregateRating = {
      "@type": "AggregateRating",
      ratingValue: profile.average_rating,
      reviewCount: profile.review_count,
    };
  }
  return payload;
}

export function seoForPublicPath(
  path: string,
  origin: string,
  data: { listings?: Listing[]; listing?: Listing | null; seller?: SellerProfile | null },
): SeoDocument {
  const listingId = listingIdFromPath(path);
  if (listingId !== null) {
    const listing = data.listing;
    if (!listing) {
      return {
        title: "Listing not found · Fooplace",
        description: "This listing is not available.",
        robots: "noindex, nofollow",
        canonical: originJoin(origin, `/listings/${listingId}/`),
        jsonLd: null,
      };
    }
    return {
      title: `${listing.dish_name} · Fooplace`,
      description: listing.description,
      robots: "index, follow",
      canonical: originJoin(origin, `/listings/${listing.id}/`),
      jsonLd: listingJsonLd(origin, listing),
    };
  }
  const sellerId = sellerIdFromPath(path);
  if (sellerId !== null) {
    const seller = data.seller;
    if (!seller) {
      return {
        title: "Seller not found · Fooplace",
        description: "This seller is not available.",
        robots: "noindex, nofollow",
        canonical: originJoin(origin, `/sellers/${sellerId}/`),
        jsonLd: null,
      };
    }
    return {
      title: `${seller.name} · Fooplace`,
      description: `Public seller profile for ${seller.name} on Fooplace.`,
      robots: "index, follow",
      canonical: originJoin(origin, `/sellers/${seller.id}/`),
      jsonLd: sellerJsonLd(origin, seller),
    };
  }
  const listings = data.listings ?? [];
  return {
    title: "Home-cooked near you · Fooplace",
    description: "Browse homemade dishes for neighbourhood pickup on Fooplace.",
    robots: "index, follow",
    canonical: originJoin(origin, "/"),
    jsonLd: browseJsonLd(origin, listings),
  };
}

export function headMarkup(doc: SeoDocument): string {
  const json = doc.jsonLd
    ? `<script type="application/ld+json">${JSON.stringify(doc.jsonLd).replaceAll("<", "\\u003c")}</script>`
    : "";
  return [
    `<title>${escapeHtml(doc.title)}</title>`,
    `<meta name="description" content="${escapeHtml(doc.description)}" />`,
    `<meta name="robots" content="${doc.robots}" />`,
    `<link rel="canonical" href="${escapeHtml(doc.canonical)}" />`,
    json,
  ].join("\n    ");
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

export function applyDocumentSeo(doc: SeoDocument): void {
  document.title = doc.title;
  upsertMeta("description", doc.description);
  upsertMeta("robots", doc.robots);
  upsertLink("canonical", doc.canonical);
  const existing = document.getElementById("fooplace-jsonld");
  if (existing) {
    existing.remove();
  }
  if (doc.jsonLd) {
    const script = document.createElement("script");
    script.id = "fooplace-jsonld";
    script.type = "application/ld+json";
    script.textContent = JSON.stringify(doc.jsonLd);
    document.head.appendChild(script);
  }
}

function upsertMeta(name: string, content: string): void {
  let meta = document.querySelector(`meta[name="${name}"]`);
  if (!meta) {
    meta = document.createElement("meta");
    meta.setAttribute("name", name);
    document.head.appendChild(meta);
  }
  meta.setAttribute("content", content);
}

function upsertLink(rel: string, href: string): void {
  let link = document.querySelector(`link[rel="${rel}"]`);
  if (!link) {
    link = document.createElement("link");
    link.setAttribute("rel", rel);
    document.head.appendChild(link);
  }
  link.setAttribute("href", href);
}
