import type { Listing, ListingSource } from "./types.ts";

const PREFIX = "/api/listings/";

async function request<T>(
  path: string,
  token: string | undefined,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${PREFIX}${path}`, { ...init, headers });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail =
      body && typeof body === "object" && "detail" in body ? String(body.detail) : "";
    throw new Error(
      detail
        ? `Backend returned HTTP ${response.status}: ${detail}`
        : `Backend returned HTTP ${response.status}`,
    );
  }
  return body as T;
}

export function apiSource(token: string): ListingSource {
  return {
    async listMine() {
      const body = await request<{ listings: Listing[] }>("mine/", token);
      return body.listings;
    },
    async listActive() {
      const body = await request<{ listings: Listing[] }>("", token);
      return body.listings;
    },
    create(input) {
      return request<Listing>("", token, { method: "POST", body: JSON.stringify(input) });
    },
    update(id, input) {
      return request<Listing>(`${id}/`, token, {
        method: "PATCH",
        body: JSON.stringify(input),
      });
    },
    async remove(id) {
      await request<{ ok: true }>(`${id}/`, token, { method: "DELETE" });
    },
  };
}

export function publicBrowse(): Promise<Listing[]> {
  return request<{ listings: Listing[] }>("", undefined).then((body) => body.listings);
}
