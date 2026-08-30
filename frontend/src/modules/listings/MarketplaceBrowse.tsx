import { TrustSignals } from "@/modules/reviews/index.ts";
import { useEffect, useState } from "react";
import { formatPickup, formatPrice } from "./format.ts";
import type { Listing, ListingSource } from "./types.ts";
import "./SellerDashboard.css";

type MarketplaceBrowseProps = {
  source: Pick<ListingSource, "listActive">;
  heading?: string;
  onOpenSeller?: (id: number) => void;
  onOrder?: (listing: Listing) => Promise<void> | void;
  onOrders?: () => void;
};

export function MarketplaceBrowse({
  source,
  heading = "Nearby dishes",
  onOpenSeller,
  onOrder,
  onOrders,
}: MarketplaceBrowseProps) {
  const [listings, setListings] = useState<Listing[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [ordering, setOrdering] = useState<number | null>(null);

  useEffect(() => {
    source
      .listActive()
      .then((items) => {
        setListings(items);
        setError(null);
      })
      .catch((loadError: unknown) => {
        setError(loadError instanceof Error ? loadError.message : "Could not load listings.");
      })
      .finally(() => setLoading(false));
  }, [source]);

  return (
    <section className="listings-page">
      <div className="listings-toolbar">
        <div>
          <h1>{heading}</h1>
          <p className="listings-lead">Homemade food for neighbourhood pickup — like Marketplace, for dinner.</p>
        </div>
        {onOrders ? (
          <button type="button" className="listings-new" onClick={onOrders}>
            Your orders
          </button>
        ) : null}
      </div>
      {error ? <p className="listings-error">{error}</p> : null}
      {loading ? <p className="listings-lead">Loading listings…</p> : null}
      {!loading && listings.length === 0 ? (
        <p className="listings-empty">No active listings yet. Sellers can publish a dish from their dashboard.</p>
      ) : null}
      <div className="listings-grid">
        {listings.map((listing) => (
          <article key={listing.id} className="listing-card">
            <img src={listing.photo} alt={listing.dish_name} />
            <div className="listing-card-body">
              <span className="listing-status">Available</span>
              <h2>{listing.dish_name}</h2>
              <p className="listing-meta">
                {formatPrice(listing.price)} · {listing.quantity_available} left
              </p>
              <p className="listing-meta">
                {listing.neighbourhood} ·{" "}
                {formatPickup(listing.pickup_date, listing.pickup_window_start, listing.pickup_window_end)}
              </p>
              <p className="listing-meta">{listing.description}</p>
              {listing.seller ? (
                <TrustSignals
                  seller={listing.seller}
                  onOpen={
                    onOpenSeller ??
                    ((sellerId) => {
                      window.location.assign(`/sellers/${sellerId}/`);
                    })
                  }
                />
              ) : (
                <p className="listing-meta">{listing.seller_name}</p>
              )}
              {onOrder ? (
                <div className="listing-card-actions">
                  <button
                    type="button"
                    disabled={ordering === listing.id}
                    onClick={() => {
                      setOrdering(listing.id);
                      Promise.resolve(onOrder(listing))
                        .catch((orderError: unknown) => {
                          setError(
                            orderError instanceof Error ? orderError.message : "Could not place the order.",
                          );
                        })
                        .finally(() => setOrdering(null));
                    }}
                  >
                    {ordering === listing.id ? "Ordering…" : "Order 1"}
                  </button>
                </div>
              ) : null}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
