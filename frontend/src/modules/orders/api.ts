import { apiGet, apiSend } from "@/shared/http.ts";
import type { BuyerNotice, IncomingOrdersResponse, Order, SellerOrder } from "./types.ts";

export function fetchOrders(token: string, signal?: AbortSignal): Promise<{ orders: Order[] }> {
  return apiGet<{ orders: Order[] }>("/api/orders/", token, signal);
}

export function fetchOrder(token: string, id: number, signal?: AbortSignal): Promise<Order> {
  return apiGet<Order>(`/api/orders/${id}/`, token, signal);
}

export function placeOrder(
  token: string,
  listingId: number,
  quantity: number,
  signal?: AbortSignal,
): Promise<Order> {
  return apiSend<Order>(
    "/api/orders/",
    token,
    "POST",
    { listing_id: listingId, quantity },
    signal,
  );
}

export function markDepositSent(token: string, id: number): Promise<Order> {
  return apiSend<Order>(`/api/orders/${id}/deposit-sent/`, token, "POST");
}

export function markPickedUp(token: string, id: number): Promise<Order> {
  return apiSend<Order>(`/api/orders/${id}/complete/`, token, "POST");
}

export function fetchIncoming(token: string): Promise<IncomingOrdersResponse> {
  return apiGet<IncomingOrdersResponse>("/api/orders/incoming/", token);
}

export function confirmOrder(token: string, orderId: number): Promise<SellerOrder> {
  return apiSend<SellerOrder>(`/api/orders/${orderId}/confirm/`, token, "POST", {
    etransfer_received: true,
  });
}

export function fetchNotifications(token: string): Promise<BuyerNotice[]> {
  return apiGet<{ notifications: BuyerNotice[] }>("/api/orders/notifications/", token).then(
    (body) => body.notifications,
  );
}
