import { useEffect, useState } from "react";
import type {
  ListingAction,
  OfficeListing,
  OfficeOrder,
  OfficeSeller,
  OfficeSource,
  OfficeSummary,
  SellerAction,
} from "./types.ts";
import "./Backoffice.css";

type Tab = "sellers" | "listings" | "orders";
type SellerFilter = "" | "pending" | "approved" | "rejected" | "flagged" | "removed";

type BackofficeProps = {
  source: OfficeSource;
};

export function Backoffice({ source }: BackofficeProps) {
  const [tab, setTab] = useState<Tab>("sellers");
  const [filter, setFilter] = useState<SellerFilter>("pending");
  const [summary, setSummary] = useState<OfficeSummary | null>(null);
  const [sellers, setSellers] = useState<OfficeSeller[]>([]);
  const [listings, setListings] = useState<OfficeListing[]>([]);
  const [orders, setOrders] = useState<OfficeOrder[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  function reload() {
    setLoading(true);
    const work = [
      source.summary().then(setSummary),
      tab === "sellers" ? source.sellers(filter).then(setSellers) : Promise.resolve(),
      tab === "listings" ? source.listings().then(setListings) : Promise.resolve(),
      tab === "orders" ? source.orders().then(setOrders) : Promise.resolve(),
    ];
    return Promise.all(work)
      .then(() => setError(null))
      .catch((loadError: unknown) => {
        setError(loadError instanceof Error ? loadError.message : "Could not load back office.");
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    void reload();
  }, [source, tab, filter]);

  return (
    <section className="office-page">
      <div>
        <h1>Back office</h1>
        <p className="office-lead">Approve sellers, review every listing and order, and use the kill switch.</p>
      </div>
      {summary ? <SummaryCards summary={summary} /> : null}
      <div className="office-tabs">
        <TabButton current={tab} id="sellers" label="Sellers" onSelect={setTab} />
        <TabButton current={tab} id="listings" label="Listings" onSelect={setTab} />
        <TabButton current={tab} id="orders" label="Orders" onSelect={setTab} />
      </div>
      {error ? <p className="office-error">{error}</p> : null}
      {loading ? <p className="office-lead">Loading…</p> : null}
      {tab === "sellers" ? (
        <SellersPanel
          sellers={sellers}
          filter={filter}
          onFilter={setFilter}
          onAction={async (seller, action, note) => {
            await source.actSeller(seller.user_id, action, note);
            await reload();
          }}
        />
      ) : null}
      {tab === "listings" ? (
        <ListingsPanel
          listings={listings}
          onAction={async (listing, action, note) => {
            await source.actListing(listing.id, action, note);
            await reload();
          }}
        />
      ) : null}
      {tab === "orders" ? <OrdersPanel orders={orders} /> : null}
    </section>
  );
}

function SummaryCards({ summary }: { summary: OfficeSummary }) {
  const cards = [
    ["Pending sellers", summary.pending_sellers],
    ["Flagged sellers", summary.flagged_sellers],
    ["Removed sellers", summary.removed_sellers],
    ["Listings", summary.listings],
    ["Flagged listings", summary.flagged_listings],
    ["Orders", summary.orders],
  ] as const;
  return (
    <div className="office-summary">
      {cards.map(([label, value]) => (
        <article key={label}>
          <strong>{value}</strong>
          {label}
        </article>
      ))}
    </div>
  );
}

function TabButton({
  current,
  id,
  label,
  onSelect,
}: {
  current: Tab;
  id: Tab;
  label: string;
  onSelect: (tab: Tab) => void;
}) {
  return (
    <button type="button" className={current === id ? "active" : undefined} onClick={() => onSelect(id)}>
      {label}
    </button>
  );
}

function SellersPanel({
  sellers,
  filter,
  onFilter,
  onAction,
}: {
  sellers: OfficeSeller[];
  filter: SellerFilter;
  onFilter: (filter: SellerFilter) => void;
  onAction: (seller: OfficeSeller, action: SellerAction, note: string) => Promise<void>;
}) {
  const filters: { id: SellerFilter; label: string }[] = [
    { id: "pending", label: "Pending" },
    { id: "approved", label: "Approved" },
    { id: "rejected", label: "Rejected" },
    { id: "flagged", label: "Flagged" },
    { id: "removed", label: "Removed" },
    { id: "", label: "All" },
  ];
  return (
    <div>
      <div className="office-filters">
        {filters.map((item) => (
          <button
            key={item.id || "all"}
            type="button"
            className={filter === item.id ? "active" : undefined}
            onClick={() => onFilter(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>
      {sellers.length === 0 ? <p className="office-lead">No sellers in this view.</p> : null}
      {sellers.map((seller) => (
        <SellerRow key={seller.user_id} seller={seller} onAction={onAction} />
      ))}
    </div>
  );
}

function SellerRow({
  seller,
  onAction,
}: {
  seller: OfficeSeller;
  onAction: (seller: OfficeSeller, action: SellerAction, note: string) => Promise<void>;
}) {
  const [note, setNote] = useState(seller.review.note);
  const profile = seller.seller;
  return (
    <table className="office-table">
      <tbody>
        <tr>
          <td>
            <strong>{seller.email || seller.user_id}</strong>
            <div>
              <span className={pillClass(seller.review)}>{sellerLabel(seller)}</span>
            </div>
            {profile ? (
              <p className="office-lead">
                {profile.has_food_handler_certification ? "Food handler cert" : "No food handler cert"}
                {" · "}
                {profile.etransfer_email}
              </p>
            ) : null}
            {profile ? (
              <p className="office-lead">
                <a href={profile.facebook_marketplace_url}>{profile.facebook_marketplace_url}</a>
              </p>
            ) : null}
          </td>
          <td>
            <input
              className="office-note"
              value={note}
              onChange={(event) => setNote(event.target.value)}
              placeholder="Note"
            />
            <div className="office-actions">
              {seller.review.status !== "approved" || seller.review.removed ? (
                <button type="button" className="ok" onClick={() => void onAction(seller, "approve", note)}>
                  Approve
                </button>
              ) : null}
              {seller.review.status === "pending" ? (
                <button type="button" className="danger" onClick={() => void onAction(seller, "reject", note)}>
                  Reject
                </button>
              ) : null}
              {seller.review.flagged ? (
                <button type="button" onClick={() => void onAction(seller, "unflag", note)}>
                  Clear flag
                </button>
              ) : (
                <button type="button" onClick={() => void onAction(seller, "flag", note)}>
                  Flag
                </button>
              )}
              {seller.review.removed || !seller.is_active ? (
                <button type="button" onClick={() => void onAction(seller, "restore", note)}>
                  Restore
                </button>
              ) : (
                <button type="button" className="danger" onClick={() => void onAction(seller, "remove", note)}>
                  Remove
                </button>
              )}
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  );
}

function ListingsPanel({
  listings,
  onAction,
}: {
  listings: OfficeListing[];
  onAction: (listing: OfficeListing, action: ListingAction, note: string) => Promise<void>;
}) {
  if (listings.length === 0) {
    return <p className="office-lead">No listings yet.</p>;
  }
  return (
    <div>
      {listings.map((listing) => (
        <ListingRow key={listing.id} listing={listing} onAction={onAction} />
      ))}
    </div>
  );
}

function ListingRow({
  listing,
  onAction,
}: {
  listing: OfficeListing;
  onAction: (listing: OfficeListing, action: ListingAction, note: string) => Promise<void>;
}) {
  const [note, setNote] = useState(listing.moderation.note);
  return (
    <table className="office-table">
      <tbody>
        <tr>
          <td>
            <strong>{listing.dish_name}</strong>
            <div>
              <span className={listing.moderation.removed ? "office-pill bad" : "office-pill"}>
                {listing.moderation.removed ? "Removed" : listing.moderation.flagged ? "Flagged" : listing.status}
              </span>
            </div>
            <p className="office-lead">
              {listing.seller_email || listing.seller_user_id} · {listing.neighbourhood} · ${listing.price} ·{" "}
              {listing.quantity_available} left
            </p>
          </td>
          <td>
            <input
              className="office-note"
              value={note}
              onChange={(event) => setNote(event.target.value)}
              placeholder="Note"
            />
            <div className="office-actions">
              {listing.moderation.flagged ? (
                <button type="button" onClick={() => void onAction(listing, "unflag", note)}>
                  Clear flag
                </button>
              ) : (
                <button type="button" onClick={() => void onAction(listing, "flag", note)}>
                  Flag
                </button>
              )}
              {listing.moderation.removed ? (
                <button type="button" onClick={() => void onAction(listing, "restore", note)}>
                  Restore
                </button>
              ) : (
                <button type="button" className="danger" onClick={() => void onAction(listing, "remove", note)}>
                  Remove
                </button>
              )}
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  );
}

function OrdersPanel({ orders }: { orders: OfficeOrder[] }) {
  if (orders.length === 0) {
    return <p className="office-lead">No orders yet.</p>;
  }
  return (
    <table className="office-table">
      <thead>
        <tr>
          <th>Dish</th>
          <th>Buyer</th>
          <th>Seller</th>
          <th>Qty</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {orders.map((order) => (
          <tr key={order.id}>
            <td>{order.dish_name}</td>
            <td>{order.buyer_email}</td>
            <td>{order.seller_email}</td>
            <td>{order.quantity}</td>
            <td>
              <span className="office-pill">{order.status}</span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function sellerLabel(seller: OfficeSeller): string {
  if (seller.review.removed || !seller.is_active) {
    return "Removed";
  }
  if (seller.review.flagged) {
    return `Flagged · ${seller.review.status}`;
  }
  return seller.review.status;
}

function pillClass(review: OfficeSeller["review"]): string {
  if (review.removed || review.status === "rejected") {
    return "office-pill bad";
  }
  if (review.flagged || review.status === "pending") {
    return "office-pill warn";
  }
  return "office-pill";
}
