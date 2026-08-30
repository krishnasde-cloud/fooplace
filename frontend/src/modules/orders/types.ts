export type OrderStatus =
  | "pending"
  | "confirmed"
  | "ready_for_pickup"
  | "completed"
  | "expired";

export type Order = {
  id: number;
  listing_id: number;
  dish_name: string;
  photos: string[];
  quantity: number;
  unit_price: string;
  total: string;
  deposit_amount: string;
  deposit_rate: string;
  deposit_sent: boolean;
  deposit_sent_at: string | null;
  status: OrderStatus;
  seller_name: string;
  seller_etransfer_email: string;
  neighbourhood: string;
  pickup_start: string;
  pickup_end: string;
  created_at: string;
};

export const ORDER_STEPS: { id: OrderStatus; label: string }[] = [
  { id: "pending", label: "Pending" },
  { id: "confirmed", label: "Confirmed" },
  { id: "ready_for_pickup", label: "Ready for pickup" },
  { id: "completed", label: "Completed" },
];
