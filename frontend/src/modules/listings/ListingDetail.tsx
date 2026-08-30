import { useEffect, useState } from "react";
import { PlaceOrder } from "@/modules/orders/PlaceOrder.tsx";
import { money, pickupWindow } from "@/shared/format.ts";
import { fetchListing } from "./api.ts";
import type { Listing } from "./types.ts";
import "./ListingDetail.css";

export function ListingDetail({ id }: { id: number }) {
  const [listing, setListing] = useState<Listing | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchListing(id, controller.signal)
      .then((payload) => {
        setListing(payload);
        setError(null);
      })
      .catch((loadError: unknown) => {
        if (loadError instanceof DOMException && loadError.name === "AbortError") {
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "Could not load listing.");
      });
    return () => controller.abort();
  }, [id]);

  if (error) {
    return (
      <section className="listing-detail">
        <a className="listing-back" href="#/">
          ← Browse listings
        </a>
        <p className="listing-status">{error}</p>
      </section>
    );
  }
  if (!listing) {
    return (
      <section className="listing-detail">
        <p>Loading listing…</p>
      </section>
    );
  }

  return (
    <section className="listing-detail">
      <a className="listing-back" href="#/">
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
        <dd>{listing.seller_name}</dd>
        <dt>Cuisine</dt>
        <dd>{listing.cuisine}</dd>
        <dt>Pickup neighbourhood</dt>
        <dd>{listing.neighbourhood}</dd>
        <dt>Pickup window</dt>
        <dd>{pickupWindow(listing.pickup_start, listing.pickup_end)}</dd>
        <dt>Available</dt>
        <dd>{listing.sold_out ? "Sold out" : `${listing.quantity_available} left`}</dd>
      </dl>
      <PlaceOrder listing={listing} />
    </section>
  );
}
