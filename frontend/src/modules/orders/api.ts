import type { BuyerNotice, IncomingOrdersResponse, SellerOrder } from "./types.ts";

const PREFIX = "/api/orders/";

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

export function fetchIncoming(token: string): Promise<IncomingOrdersResponse> {
  return request<IncomingOrdersResponse>("incoming/", token);
}

export function confirmOrder(token: string, orderId: number): Promise<SellerOrder> {
  return request<SellerOrder>(`${orderId}/confirm/`, token, {
    method: "POST",
    body: JSON.stringify({ etransfer_received: true }),
  });
}

export function fetchNotifications(token: string): Promise<BuyerNotice[]> {
  return request<{ notifications: BuyerNotice[] }>("notifications/", token).then(
    (body) => body.notifications,
  );
}
