import type { ReactNode } from "react";
import { money, pickupWindow } from "@/shared/format.ts";
import type { Listing } from "@/modules/listings/types.ts";
import { formatJoined, formatRating, TrustSignals } from "@/modules/reviews/TrustSignals.tsx";
import type { SellerProfile } from "@/modules/reviews/types.ts";
import { paths } from "@/app/route.ts";
import "@/modules/listings/BrowseListings.css";
import "@/modules/listings/ListingDetail.css";
import "@/modules/reviews/TrustSignals.css";

export function PublicBrowse({ listings }: { listings: Listing[] }) {
  return (
    <section className="browse">
      <h1>Home-cooked near you</h1>
      <p className="browse-lead">Filter by neighbourhood or cuisine, then place an order.</p>
      {listings.length === 0 ? (
        <p className="browse-empty">No listings match those filters.</p>
      ) : (
        <ul className="listing-grid">
          {listings.map((listing) => (
            <ListingCard key={listing.id} listing={listing} />
          ))}
        </ul>
      )}
    </section>
  );
}

export function ListingCard({ listing }: { listing: Listing }) {
  const photo = listing.photos[0];
  return (
    <li>
      <a className="listing-card" href={paths.listing(listing.id)}>
        {photo ? (
          <img src={photo} alt={listing.dish_name} />
        ) : (
          <div className="listing-photo-fallback">No photo</div>
        )}
        <h2>{listing.dish_name}</h2>
        <p className="listing-meta">
          {listing.cuisine} · {listing.neighbourhood}
          {listing.sold_out ? " · Sold out" : ""}
        </p>
        <p className="listing-meta">
          {listing.seller
            ? `${listing.seller.name}${listing.seller.has_food_handler_certification ? " · Food handler certified" : ""}${
                listing.seller.average_rating != null
                  ? ` · ★ ${listing.seller.average_rating.toFixed(1)}`
                  : ""
              }`
            : listing.seller_name}
        </p>
        <p className="listing-price">{money(listing.price)}</p>
      </a>
    </li>
  );
}

export function PublicListing({ listing, children }: { listing: Listing; children?: ReactNode }) {
  return (
    <section className="listing-detail">
      <a className="listing-back" href={paths.browse}>
        ← Browse listings
      </a>
      <h1>{listing.dish_name}</h1>
      {listing.photos.length > 0 ? (
        <ul className="listing-photos">
          {listing.photos.map((photo) => (
            <li key={photo}>
              <img src={photo} alt={listing.dish_name} />
            </li>
          ))}
        </ul>
      ) : (
        <div className="listing-photo-fallback">No photos yet</div>
      )}
      <p>{listing.description}</p>
      <dl className="listing-facts">
        <dt>Price</dt>
        <dd>{money(listing.price)}</dd>
        <dt>Seller</dt>
        <dd>
          {listing.seller ? (
            <a href={paths.seller(listing.seller.id)}>
              <TrustSignals seller={listing.seller} />
            </a>
          ) : (
            listing.seller_name
          )}
        </dd>
        <dt>Cuisine</dt>
        <dd>{listing.cuisine}</dd>
        <dt>Pickup neighbourhood</dt>
        <dd>{listing.neighbourhood}</dd>
        <dt>Pickup window</dt>
        <dd>{pickupWindow(listing.pickup_start, listing.pickup_end)}</dd>
        <dt>Available</dt>
        <dd>{listing.sold_out ? "Sold out" : `${listing.quantity_available} left`}</dd>
      </dl>
      {children}
    </section>
  );
}

export function PublicSeller({ seller }: { seller: SellerProfile }) {
  return (
    <section className="listings-page">
      <h1>{seller.name}</h1>
      <p className="listings-lead">Public profile and reviews from completed orders.</p>
      <TrustSignals seller={seller} />
      <p>Joined {formatJoined(seller.joined_at)}</p>
      <p>Completed orders {seller.completed_orders}</p>
      <p>Rating {formatRating(seller)}</p>
      <h2>Reviews</h2>
      {seller.reviews.length === 0 ? (
        <p>No reviews yet. Buyers can rate a seller after pickup.</p>
      ) : (
        seller.reviews.map((review) => (
          <article key={review.id}>
            <strong>
              {"★".repeat(review.stars)}
              {"☆".repeat(5 - review.stars)} · {review.buyer_name}
            </strong>
            {review.comment ? <p>{review.comment}</p> : null}
          </article>
        ))
      )}
    </section>
  );
}

export function PublicMissing({ message }: { message: string }) {
  return (
    <section className="listing-detail">
      <a className="listing-back" href={paths.browse}>
        ← Browse listings
      </a>
      <p className="listing-status">{message}</p>
    </section>
  );
}
