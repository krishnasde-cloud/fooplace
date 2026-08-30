export type OrderStatus =
  | "pending"
  | "confirmed"
  | "picked_up"
  | "cancelled"
  | "expired";

export type OrderHistoryEvent = {
  id: number;
  status: OrderStatus;
  note: string;
  created_at: string;
};

export type SellerOrder = {
  id: number;
  listing_id: number;
  dish_name: string;
  quantity: number;
  status: OrderStatus;
  created_at: string;
  confirm_by: string;
  buyer_email: string;
  unit_price: string;
  history: OrderHistoryEvent[];
};

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
