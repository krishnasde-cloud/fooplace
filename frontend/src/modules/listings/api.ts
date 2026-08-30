import { apiGet } from "@/shared/http.ts";
import type { Listing, ListingCatalog } from "./types.ts";

export function fetchListings(
  filters: { neighbourhood?: string; cuisine?: string; q?: string },
  signal?: AbortSignal,
): Promise<ListingCatalog> {
  const params = new URLSearchParams();
  if (filters.neighbourhood) {
    params.set("neighbourhood", filters.neighbourhood);
  }
  if (filters.cuisine) {
    params.set("cuisine", filters.cuisine);
  }
  if (filters.q) {
    params.set("q", filters.q);
  }
  const query = params.toString();
  return apiGet<ListingCatalog>(`/api/listings/${query ? `?${query}` : ""}`, null, signal);
}

export function fetchListing(id: number, signal?: AbortSignal): Promise<Listing> {
  return apiGet<Listing>(`/api/listings/${id}/`, null, signal);
}
