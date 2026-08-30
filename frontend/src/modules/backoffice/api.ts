import type {
  OfficeListing,
  OfficeOrder,
  OfficeSeller,
  OfficeSource,
  OfficeSummary,
} from "./types.ts";

const PREFIX = "/api/backoffice/";

async function request<T>(path: string, token: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${token}`);
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

export function apiOffice(token: string): OfficeSource {
  return {
    summary: () => request<OfficeSummary>("", token),
    sellers(status) {
      const query = status ? `?status=${encodeURIComponent(status)}` : "";
      return request<{ sellers: OfficeSeller[] }>(`sellers/${query}`, token).then(
        (body) => body.sellers,
      );
    },
    actSeller(userId, action, note = "") {
      return request<OfficeSeller>(`sellers/${userId}/`, token, {
        method: "POST",
        body: JSON.stringify({ action, note }),
      });
    },
    listings() {
      return request<{ listings: OfficeListing[] }>("listings/", token).then(
        (body) => body.listings,
      );
    },
    actListing(listingId, action, note = "") {
      return request<OfficeListing>(`listings/${listingId}/`, token, {
        method: "POST",
        body: JSON.stringify({ action, note }),
      });
    },
    orders() {
      return request<{ orders: OfficeOrder[] }>("orders/", token).then((body) => body.orders);
    },
  };
}
