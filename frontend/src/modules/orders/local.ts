import { confirmOrder, fetchIncoming } from "./api.ts";
import type { IncomingOrdersResponse, SellerOrder } from "./types.ts";

const KEY = "fooplace.sellerOrders";

export type OrderSource = {
  incoming: () => Promise<IncomingOrdersResponse>;
  confirm: (orderId: number) => Promise<SellerOrder>;
};

function load(): SellerOrder[] {
  const raw = localStorage.getItem(KEY);
  if (!raw) {
    return [];
  }
  try {
    return JSON.parse(raw) as SellerOrder[];
  } catch {
    return [];
  }
}

function save(orders: SellerOrder[]): void {
  localStorage.setItem(KEY, JSON.stringify(orders));
}

function now(): string {
  return new Date().toISOString();
}

function samplePending(): SellerOrder {
  const created = now();
  const confirmBy = new Date(Date.now() + 4 * 60 * 60 * 1000).toISOString();
  return {
    id: Date.now(),
    listing_id: 1,
    dish_name: "Butter chicken",
    photos: [],
    quantity: 2,
    status: "pending",
    created_at: created,
    confirm_by: confirmBy,
    buyer_email: "buyer@example.com",
    unit_price: "14.00",
    total: "28.00",
    deposit_amount: "14.00",
    deposit_rate: "0.50",
    deposit_sent: false,
    deposit_sent_at: null,
    seller_name: "seller@example.com",
    seller_etransfer_email: "seller@example.com",
    neighbourhood: "Kensington",
    pickup_start: created,
    pickup_end: confirmBy,
    history: [
      {
        id: 1,
        status: "pending",
        note: "created",
        created_at: created,
      },
    ],
  };
}

export function localSource(): OrderSource {
  return {
    async incoming() {
      const orders = load();
      if (!orders.length) {
        const seeded = [samplePending()];
        save(seeded);
        return { confirm_hours: 4, orders: seeded };
      }
      return { confirm_hours: 4, orders };
    },
    async confirm(orderId) {
      const orders = load();
      const index = orders.findIndex((order) => order.id === orderId);
      if (index < 0) {
        throw new Error("Order not found");
      }
      const current = orders[index];
      if (current.status !== "pending") {
        throw new Error("Backend returned HTTP 400: invalid_status");
      }
      const next: SellerOrder = {
        ...current,
        status: "confirmed",
        history: [
          ...current.history,
          {
            id: current.history.length + 1,
            status: "confirmed",
            note: "seller confirmed after checking e-transfer inbox",
            created_at: now(),
          },
        ],
      };
      orders[index] = next;
      save(orders);
      return next;
    },
  };
}

export function apiOrderSource(token: string): OrderSource {
  return {
    incoming: () => fetchIncoming(token),
    confirm: (orderId) => confirmOrder(token, orderId),
  };
}
