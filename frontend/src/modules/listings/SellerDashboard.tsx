import { useEffect, useState } from "react";
import { formatExpiry, formatOrders, formatPickup, formatPrice, listingExpired } from "./format.ts";
import { ListingForm } from "./ListingForm.tsx";
import type { Listing, ListingInput, ListingSource } from "./types.ts";
import "./SellerDashboard.css";

type SellerDashboardProps = {
  source: ListingSource;
  onPublicProfile?: () => void;
};

type View = { kind: "list" } | { kind: "create" } | { kind: "edit"; listing: Listing };

export function SellerDashboard({ source, onPublicProfile }: SellerDashboardProps) {
  const [listings, setListings] = useState<Listing[]>([]);
  const [view, setView] = useState<View>({ kind: "list" });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  function refresh() {
    return source
      .listMine()
      .then((items) => {
        setListings(items);
        setError(null);
      })
      .catch((loadError: unknown) => {
        setError(loadError instanceof Error ? loadError.message : "Could not load listings.");
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    void refresh();
  }, [source]);

  async function save(input: ListingInput, id?: number) {
    if (id === undefined) {
      await source.create(input);
    } else {
      await source.update(id, input);
    }
    await refresh();
    setView({ kind: "list" });
  }

  if (view.kind === "create") {
    return (
      <ListingForm
        submitLabel="Publish listing"
        onCancel={() => setView({ kind: "list" })}
        onSubmit={(input) => save(input)}
      />
    );
  }
  if (view.kind === "edit") {
    return (
      <ListingForm
        initial={view.listing}
        submitLabel="Save changes"
        onCancel={() => setView({ kind: "list" })}
        onSubmit={(input) => save(input, view.listing.id)}
      />
    );
  }

  const expired = listings.filter((listing) => listingExpired(listing));
  const active = listings.filter((listing) => listing.status === "active" && !listingExpired(listing));
  const sold = listings.filter((listing) => listing.status === "sold_out" && !listingExpired(listing));

  return (
    <section className="listings-page">
      <div className="listings-toolbar">
        <div>
          <h1>Your listings</h1>
          <p className="listings-lead">
            Active dishes stay live for 24 hours. Re-list an expired dish to publish it again.
          </p>
        </div>
        <div className="listing-card-actions">
          {onPublicProfile ? (
            <button type="button" onClick={onPublicProfile}>
              Public profile
            </button>
          ) : null}
          <button type="button" className="listings-new" onClick={() => setView({ kind: "create" })}>
            New listing
          </button>
        </div>
      </div>
      {error ? <p className="listings-error">{error}</p> : null}
      {loading ? <p className="listings-lead">Loading listings…</p> : null}
      {!loading && listings.length === 0 ? (
        <p className="listings-empty">No listings yet. Publish a dish with a photo, neighbourhood, and pickup window.</p>
      ) : null}
      {active.length ? (
        <ListingGroup
          title="Active"
          listings={active}
          onEdit={(listing) => setView({ kind: "edit", listing })}
          onSoldOut={async (listing) => {
            await source.update(listing.id, { status: "sold_out" });
            await refresh();
          }}
          onDelete={async (listing) => {
            if (!window.confirm(`Delete ${listing.dish_name}?`)) {
              return;
            }
            await source.remove(listing.id);
            await refresh();
          }}
        />
      ) : null}
      {sold.length ? (
        <ListingGroup
          title="Sold out"
          listings={sold}
          onEdit={(listing) => setView({ kind: "edit", listing })}
          onSoldOut={undefined}
          onDelete={async (listing) => {
            if (!window.confirm(`Delete ${listing.dish_name}?`)) {
              return;
            }
            await source.remove(listing.id);
            await refresh();
          }}
        />
      ) : null}
      {expired.length ? (
        <ListingGroup
          title="Expired"
          listings={expired}
          onEdit={(listing) => setView({ kind: "edit", listing })}
          onRelist={async (listing) => {
            try {
              await source.relist(listing.id);
              await refresh();
            } catch (relistError: unknown) {
              setError(relistError instanceof Error ? relistError.message : "Could not re-list.");
            }
          }}
          onDelete={async (listing) => {
            if (!window.confirm(`Delete ${listing.dish_name}?`)) {
              return;
            }
            await source.remove(listing.id);
            await refresh();
          }}
        />
      ) : null}
    </section>
  );
}

type ListingGroupProps = {
  title: string;
  listings: Listing[];
  onEdit: (listing: Listing) => void;
  onSoldOut?: (listing: Listing) => Promise<void>;
  onRelist?: (listing: Listing) => Promise<void>;
  onDelete: (listing: Listing) => Promise<void>;
};

function ListingGroup({ title, listings, onEdit, onSoldOut, onRelist, onDelete }: ListingGroupProps) {
  return (
    <div className="listings-grid">
      <h2 className="listings-lead">{title}</h2>
      {listings.map((listing) => {
        const expired = listingExpired(listing);
        return (
          <article key={listing.id} className="listing-card">
            <img src={listing.photo} alt={listing.dish_name} />
            <div className="listing-card-body">
              <span
                className={`listing-status${expired ? " expired" : listing.status === "sold_out" ? " sold" : ""}`}
              >
                {expired ? "Expired" : listing.status === "sold_out" ? "Sold out" : "Active"}
              </span>
              <h2>{listing.dish_name}</h2>
              <p className="listing-meta">
                {formatPrice(listing.price)} · {listing.quantity_available} left
              </p>
              <p className="listing-meta">
                {listing.neighbourhood} ·{" "}
                {formatPickup(listing.pickup_date, listing.pickup_window_start, listing.pickup_window_end)}
              </p>
              <p className="listing-meta">{formatExpiry(listing.expires_at, expired)}</p>
              <p className="listing-meta">Orders: {formatOrders(listing.order_status)}</p>
              <div className="listing-card-actions">
                {onRelist ? (
                  <button type="button" className="relist" onClick={() => void onRelist(listing)}>
                    Re-list
                  </button>
                ) : null}
                <button type="button" onClick={() => onEdit(listing)}>
                  Edit
                </button>
                {onSoldOut ? (
                  <button type="button" onClick={() => void onSoldOut(listing)}>
                    Mark sold out
                  </button>
                ) : null}
                <button type="button" className="danger" onClick={() => void onDelete(listing)}>
                  Delete
                </button>
              </div>
            </div>
          </article>
        );
      })}
    </div>
  );
}
