import type { BuyerOrder, Review, ReviewsSource, SellerProfile } from "./types.ts";

async function request<T>(path: string, token: string | undefined, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(path, { ...init, headers });
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

export function reviewsApi(token: string): ReviewsSource {
  return {
    sellerProfile(id) {
      return request<SellerProfile>(`/api/reviews/sellers/${id}/`, token);
    },
    async myOrders() {
      const body = await request<{ orders: BuyerOrder[] }>("/api/reviews/orders/", token);
      return body.orders;
    },
    completeOrder(id) {
      return request<BuyerOrder>(`/api/reviews/orders/${id}/complete/`, token, { method: "POST" });
    },
    leaveReview(orderId, stars, comment) {
      return request<Review>("/api/reviews/", token, {
        method: "POST",
        body: JSON.stringify({ order_id: orderId, stars, comment }),
      });
    },
    placeOrder(listingId, quantity = 1) {
      return request(`/api/listings/${listingId}/orders/`, token, {
        method: "POST",
        body: JSON.stringify({ quantity }),
      });
    },
  };
}

export function publicSellerProfile(id: number): Promise<SellerProfile> {
  return request<SellerProfile>(`/api/reviews/sellers/${id}/`, undefined);
}
