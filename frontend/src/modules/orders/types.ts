export type OrderStatus =
  | "pending"
  | "confirmed"
  | "ready_for_pickup"
  | "completed"
  | "expired"
  | "picked_up"
  | "cancelled";

export type OrderHistoryEvent = {
  id: number;
  status: OrderStatus;
  note: string;
  created_at: string;
};

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
  seller_id?: number;
  seller_name: string;
  seller_etransfer_email: string;
  neighbourhood: string;
  pickup_start: string;
  pickup_end: string;
  created_at: string;
  confirm_by: string;
  buyer_email: string;
  history: OrderHistoryEvent[];
};

export type SellerOrder = Order;

export type IncomingOrdersResponse = {
  confirm_hours: number;
  orders: SellerOrder[];
};

export type BuyerNotice = {
  id: number;
  order_id: number;
  kind: "expired" | "confirmed";
  message: string;
  created_at: string;
  read_at: string | null;
  dish_name: string;
};

export const ORDER_STEPS: { id: OrderStatus; label: string }[] = [
  { id: "pending", label: "Pending" },
  { id: "confirmed", label: "Confirmed" },
  { id: "ready_for_pickup", label: "Ready for pickup" },
  { id: "completed", label: "Completed" },
];
