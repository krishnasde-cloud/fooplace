import { listingExpired } from "./format.ts";
import type { Listing, ListingSource, OrderStatusCounts } from "./types.ts";

const KEY = "fooplace.sellerListings";

const EMPTY_ORDERS: OrderStatusCounts = {
  pending: 0,
  confirmed: 0,
  ready_for_pickup: 0,
  completed: 0,
  expired: 0,
  picked_up: 0,
  cancelled: 0,
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

function expiresAt(from = Date.now()): string {
  return new Date(from + 24 * 60 * 60 * 1000).toISOString();
}

function extras(input: {
  photo: string;
  neighbourhood: string;
  pickup_date: string;
  pickup_window_start: string;
  pickup_window_end: string;
  cuisine?: string;
  quantity_available: number;
  status?: Listing["status"];
}): Pick<Listing, "cuisine" | "photos" | "sold_out" | "seller_name" | "pickup_start" | "pickup_end"> {
  const soldOut = input.quantity_available === 0 || input.status === "sold_out";
  return {
    cuisine: input.cuisine ?? "",
    photos: input.photo ? [input.photo] : [],
    sold_out: soldOut,
    seller_name: "You",
    pickup_start: `${input.pickup_date}T${input.pickup_window_start}`,
    pickup_end: `${input.pickup_date}T${input.pickup_window_end}`,
  };
}

export function localSource(): ListingSource {
  return {
    async listMine() {
      return load();
    },
    async listActive() {
      return load().filter((listing) => listing.status === "active" && !listingExpired(listing));
    },
    async create(input) {
      const listings = load();
      const status = input.quantity_available === 0 ? "sold_out" : (input.status ?? "active");
      const created: Listing = {
        id: Date.now(),
        ...input,
        price: Number(input.price).toFixed(2),
        status,
        expires_at: expiresAt(),
        expired: false,
        created_at: now(),
        updated_at: now(),
        order_status: EMPTY_ORDERS,
        ...extras({ ...input, status }),
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
      const status = quantity === 0 ? "sold_out" : (input.status ?? current.status);
      const merged = { ...current, ...input, status, quantity_available: quantity };
      const next: Listing = {
        ...merged,
        price: input.price !== undefined ? Number(input.price).toFixed(2) : current.price,
        updated_at: now(),
        ...extras(merged),
      };
      listings[index] = next;
      save(listings);
      return next;
    },
    async relist(id) {
      const listings = load();
      const index = listings.findIndex((listing) => listing.id === id);
      if (index < 0) {
        throw new Error("Listing not found");
      }
      const current = listings[index];
      if (!listingExpired(current)) {
        throw new Error("Listing is still live");
      }
      if (current.quantity_available < 1) {
        throw new Error("Add quantity before re-listing");
      }
      const next: Listing = {
        ...current,
        status: "active",
        expires_at: expiresAt(),
        expired: false,
        updated_at: now(),
        sold_out: false,
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
