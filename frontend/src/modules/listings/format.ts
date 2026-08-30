import type { OrderStatusCounts } from "./types.ts";

export function formatPrice(price: string): string {
  const amount = Number(price);
  if (Number.isNaN(amount)) {
    return `$${price}`;
  }
  return `$${amount.toFixed(2)}`;
}

export function formatPickup(date: string, start: string, end: string): string {
  const day = new Date(`${date}T00:00:00`);
  const when = Number.isNaN(day.getTime())
    ? date
    : day.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
  return `${when} · ${formatClock(start)}–${formatClock(end)}`;
}

export function formatExpiry(expiresAt: string, expired: boolean): string {
  if (expired || listingExpired({ expires_at: expiresAt, expired })) {
    return "Expired after 24 hours";
  }
  const end = new Date(expiresAt);
  if (Number.isNaN(end.getTime())) {
    return "Live for 24 hours";
  }
  return `Live until ${end.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  })}`;
}

export function listingExpired(listing: { expires_at?: string; expired?: boolean }): boolean {
  if (listing.expired) {
    return true;
  }
  if (!listing.expires_at) {
    return false;
  }
  return Date.parse(listing.expires_at) <= Date.now();
}

export function formatOrders(counts: OrderStatusCounts): string {
  const parts = [
    counts.pending ? `${counts.pending} pending` : "",
    counts.confirmed ? `${counts.confirmed} confirmed` : "",
    counts.ready_for_pickup ? `${counts.ready_for_pickup} ready` : "",
    counts.picked_up ? `${counts.picked_up} picked up` : "",
    counts.completed ? `${counts.completed} completed` : "",
  ].filter(Boolean);
  return parts.length ? parts.join(" · ") : "No orders yet";
}

function formatClock(value: string): string {
  const [hours, minutes] = value.split(":");
  const date = new Date();
  date.setHours(Number(hours), Number(minutes || 0), 0, 0);
  if (Number.isNaN(date.getTime())) {
    return value.slice(0, 5);
  }
  return date.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
}
