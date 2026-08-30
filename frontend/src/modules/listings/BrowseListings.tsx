import { useEffect, useState } from "react";
import { money } from "@/shared/format.ts";
import { fetchListings } from "./api.ts";
import type { Listing, ListingCatalog } from "./types.ts";
import "./BrowseListings.css";

export function BrowseListings() {
  const [neighbourhood, setNeighbourhood] = useState("");
  const [cuisine, setCuisine] = useState("");
  const [query, setQuery] = useState("");
  const [catalog, setCatalog] = useState<ListingCatalog | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchListings(
      { neighbourhood, cuisine, q: query.trim() || undefined },
      controller.signal,
    )
      .then((payload) => {
        setCatalog(payload);
        setError(null);
      })
      .catch((loadError: unknown) => {
        if (loadError instanceof DOMException && loadError.name === "AbortError") {
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "Could not load listings.");
      });
    return () => controller.abort();
  }, [neighbourhood, cuisine, query]);

  return (
    <section className="browse">
      <h1>Home-cooked near you</h1>
      <p className="browse-lead">Filter by neighbourhood or cuisine, then place an order.</p>

      <div className="browse-filters">
        <label>
          Search
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Dish name"
          />
        </label>
        <label>
          Neighbourhood
          <select value={neighbourhood} onChange={(event) => setNeighbourhood(event.target.value)}>
            <option value="">All neighbourhoods</option>
            {(catalog?.filters.neighbourhoods ?? []).map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Cuisine
          <select value={cuisine} onChange={(event) => setCuisine(event.target.value)}>
            <option value="">All cuisines</option>
            {(catalog?.filters.cuisines ?? []).map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error ? <p className="browse-error">{error}</p> : null}
      {!catalog && !error ? <p className="browse-pending">Loading listings…</p> : null}
      {catalog && catalog.listings.length === 0 ? (
        <p className="browse-empty">No listings match those filters.</p>
      ) : null}
      {catalog ? (
        <ul className="listing-grid">
          {catalog.listings.map((listing) => (
            <ListingCard key={listing.id} listing={listing} />
          ))}
        </ul>
      ) : null}
    </section>
  );
}

function ListingCard({ listing }: { listing: Listing }) {
  const photo = listing.photos[0];
  return (
    <li>
      <a className="listing-card" href={`#/listings/${listing.id}`}>
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
        <p className="listing-price">{money(listing.price)}</p>
      </a>
    </li>
  );
}
