import type { Listing, ListingSource, OrderStatusCounts } from "./types.ts";

const KEY = "fooplace.sellerListings";

const EMPTY_ORDERS: OrderStatusCounts = {
  pending: 0,
  confirmed: 0,
  picked_up: 0,
  cancelled: 0,
  expired: 0,
};

function load(): Listing[] {
  const raw = localStorage.getItem(KEY);
  if (!raw) {
    return [];
  }
  try {
    return JSON.parse(raw) as Listing[];
  } catch {
    return [];
  }
}

function save(listings: Listing[]): void {
  localStorage.setItem(KEY, JSON.stringify(listings));
}

function now(): string {
  return new Date().toISOString();
}

export function localSource(): ListingSource {
  return {
    async listMine() {
      return load();
    },
    async listActive() {
      return load().filter((listing) => listing.status === "active");
    },
    async create(input) {
      const listings = load();
      const created: Listing = {
        id: Date.now(),
        ...input,
        price: Number(input.price).toFixed(2),
        status: input.quantity_available === 0 ? "sold_out" : (input.status ?? "active"),
        created_at: now(),
        updated_at: now(),
        order_status: EMPTY_ORDERS,
      };
      listings.unshift(created);
      save(listings);
      return created;
    },
    async update(id, input) {
      const listings = load();
      const index = listings.findIndex((listing) => listing.id === id);
      if (index < 0) {
        throw new Error("Listing not found");
      }
      const current = listings[index];
      const quantity = input.quantity_available ?? current.quantity_available;
      const next: Listing = {
        ...current,
        ...input,
        price: input.price !== undefined ? Number(input.price).toFixed(2) : current.price,
        status: quantity === 0 ? "sold_out" : (input.status ?? current.status),
        updated_at: now(),
      };
      listings[index] = next;
      save(listings);
      return next;
    },
    async remove(id) {
      save(load().filter((listing) => listing.id !== id));
    },
  };
}
