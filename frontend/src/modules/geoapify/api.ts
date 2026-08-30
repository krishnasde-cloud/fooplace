import type { Place } from "./types.ts";

const PREFIX = "/api/geoapify/";

export async function autocompleteAddress(
  text: string,
  signal?: AbortSignal,
): Promise<Place[]> {
  const query = new URLSearchParams({ text });
  const response = await fetch(`${PREFIX}autocomplete/?${query}`, { signal });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    return [];
  }
  if (!body || typeof body !== "object" || !Array.isArray(body.results)) {
    return [];
  }
  return body.results as Place[];
}
